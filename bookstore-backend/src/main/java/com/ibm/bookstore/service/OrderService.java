package com.ibm.bookstore.service;

import com.ibm.bookstore.dto.*;
import com.ibm.bookstore.exception.BusinessException;
import com.ibm.bookstore.exception.ResourceNotFoundException;
import com.ibm.bookstore.model.*;
import com.ibm.bookstore.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository  orderRepository;
    private final CartRepository   cartRepository;
    private final BookRepository   bookRepository;

    @Transactional
    public OrderResponse placeOrder(Long userId, OrderRequest req) {
        Cart cart = cartRepository.findByUserId(userId)
                .orElseThrow(() -> new BusinessException("Cart is empty"));

        if (cart.getItems().isEmpty()) {
            throw new BusinessException("Cannot place an order with an empty cart");
        }

        Order order = Order.builder()
                .user(User.builder().id(userId).build())
                .shippingAddress(req.shippingAddress())
                .shippingCity(req.shippingCity())
                .shippingCountry(req.shippingCountry())
                .shippingPostalCode(req.shippingPostalCode())
                .status(OrderStatus.PENDING)
                .totalAmount(BigDecimal.ZERO)
                .build();

        BigDecimal total = BigDecimal.ZERO;
        for (CartItem ci : cart.getItems()) {
            Book book = bookRepository.findById(ci.getBook().getId())
                    .orElseThrow(() -> new ResourceNotFoundException("Book", ci.getBook().getId()));

            if (book.getStockQuantity() < ci.getQuantity()) {
                throw new BusinessException("Insufficient stock for: " + book.getTitle());
            }
            book.setStockQuantity(book.getStockQuantity() - ci.getQuantity());
            bookRepository.save(book);

            BigDecimal lineTotal = book.getPrice().multiply(BigDecimal.valueOf(ci.getQuantity()));
            total = total.add(lineTotal);

            OrderItem oi = OrderItem.builder()
                    .order(order)
                    .book(book)
                    .quantity(ci.getQuantity())
                    .unitPrice(book.getPrice())
                    .build();
            order.getItems().add(oi);
        }

        order.setTotalAmount(total);
        order = orderRepository.save(order);

        // clear cart after successful order
        cart.getItems().clear();
        cartRepository.save(cart);

        return toDto(order);
    }

    @Transactional(readOnly = true)
    public Page<OrderResponse> getMyOrders(Long userId, Pageable pageable) {
        return orderRepository.findByUserId(userId, pageable).map(this::toDto);
    }

    @Transactional(readOnly = true)
    public OrderResponse getOrder(Long userId, Long orderId) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new ResourceNotFoundException("Order", orderId));
        if (!order.getUser().getId().equals(userId)) {
            throw new BusinessException("Order does not belong to the current user");
        }
        return toDto(order);
    }

    // Admin operations
    @Transactional(readOnly = true)
    public Page<OrderResponse> getAllOrders(Pageable pageable) {
        return orderRepository.findAll(pageable).map(this::toDto);
    }

    @Transactional
    public OrderResponse updateStatus(Long orderId, OrderStatus status) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new ResourceNotFoundException("Order", orderId));
        order.setStatus(status);
        return toDto(orderRepository.save(order));
    }

    // ── helpers ──────────────────────────────────────────────────────────────

    private OrderResponse toDto(Order o) {
        List<OrderItemResponse> items = o.getItems().stream()
                .map(i -> new OrderItemResponse(
                        i.getBook().getId(),
                        i.getBook().getTitle(),
                        i.getQuantity(),
                        i.getUnitPrice(),
                        i.getUnitPrice().multiply(BigDecimal.valueOf(i.getQuantity()))
                ))
                .toList();

        return new OrderResponse(
                o.getId(), o.getStatus(), o.getTotalAmount(),
                o.getShippingAddress(), o.getShippingCity(),
                o.getShippingCountry(), o.getShippingPostalCode(),
                items, o.getCreatedAt()
        );
    }
}
