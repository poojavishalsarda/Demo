package com.ibm.bookstore.service;

import com.ibm.bookstore.dto.*;
import com.ibm.bookstore.exception.BusinessException;
import com.ibm.bookstore.exception.ResourceNotFoundException;
import com.ibm.bookstore.model.*;
import com.ibm.bookstore.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

@Service
@RequiredArgsConstructor
public class CartService {

    private final CartRepository cartRepository;
    private final BookRepository bookRepository;

    @Transactional(readOnly = true)
    public CartResponse getCart(Long userId) {
        Cart cart = getOrCreateCart(userId);
        return toDto(cart);
    }

    @Transactional
    public CartResponse addItem(Long userId, CartItemRequest req) {
        Cart cart = getOrCreateCart(userId);
        Book book = bookRepository.findById(req.bookId())
                .orElseThrow(() -> new ResourceNotFoundException("Book", req.bookId()));

        if (book.getStockQuantity() < req.quantity()) {
            throw new BusinessException("Insufficient stock for book: " + book.getTitle());
        }

        cart.getItems().stream()
                .filter(i -> i.getBook().getId().equals(req.bookId()))
                .findFirst()
                .ifPresentOrElse(
                        i -> i.setQuantity(i.getQuantity() + req.quantity()),
                        () -> cart.getItems().add(
                                CartItem.builder().cart(cart).book(book).quantity(req.quantity()).build()
                        )
                );
        return toDto(cartRepository.save(cart));
    }

    @Transactional
    public CartResponse updateItem(Long userId, Long bookId, int quantity) {
        Cart cart = getOrCreateCart(userId);
        CartItem item = cart.getItems().stream()
                .filter(i -> i.getBook().getId().equals(bookId))
                .findFirst()
                .orElseThrow(() -> new ResourceNotFoundException("Cart item not found for bookId: " + bookId));

        if (quantity <= 0) {
            cart.getItems().remove(item);
        } else {
            Book book = item.getBook();
            if (book.getStockQuantity() < quantity) {
                throw new BusinessException("Insufficient stock for book: " + book.getTitle());
            }
            item.setQuantity(quantity);
        }
        return toDto(cartRepository.save(cart));
    }

    @Transactional
    public CartResponse removeItem(Long userId, Long bookId) {
        Cart cart = getOrCreateCart(userId);
        cart.getItems().removeIf(i -> i.getBook().getId().equals(bookId));
        return toDto(cartRepository.save(cart));
    }

    @Transactional
    public void clearCart(Long userId) {
        Cart cart = getOrCreateCart(userId);
        cart.getItems().clear();
        cartRepository.save(cart);
    }

    // ── helpers ──────────────────────────────────────────────────────────────

    private Cart getOrCreateCart(Long userId) {
        return cartRepository.findByUserId(userId).orElseGet(() -> {
            Cart c = Cart.builder()
                    .user(User.builder().id(userId).build())
                    .build();
            return cartRepository.save(c);
        });
    }

    private CartResponse toDto(Cart cart) {
        List<CartItemResponse> items = cart.getItems().stream()
                .map(i -> new CartItemResponse(
                        i.getId(),
                        i.getBook().getId(),
                        i.getBook().getTitle(),
                        i.getBook().getAuthor(),
                        i.getBook().getImageUrl(),
                        i.getBook().getPrice(),
                        i.getQuantity(),
                        i.getBook().getPrice().multiply(BigDecimal.valueOf(i.getQuantity()))
                ))
                .toList();

        BigDecimal total = items.stream()
                .map(CartItemResponse::subTotal)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        return new CartResponse(cart.getId(), items, total);
    }
}
