package com.ibm.bookstore.controller;

import com.ibm.bookstore.dto.*;
import com.ibm.bookstore.model.User;
import com.ibm.bookstore.service.OrderService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/orders")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;

    /**
     * POST /api/v1/orders
     * Place an order from the current user's cart.
     */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public OrderResponse placeOrder(@AuthenticationPrincipal User user,
                                    @Valid @RequestBody OrderRequest request) {
        return orderService.placeOrder(user.getId(), request);
    }

    /** GET /api/v1/orders — current user's orders */
    @GetMapping
    public Page<OrderResponse> getMyOrders(@AuthenticationPrincipal User user,
                                           Pageable pageable) {
        return orderService.getMyOrders(user.getId(), pageable);
    }

    /** GET /api/v1/orders/{id} */
    @GetMapping("/{id}")
    public OrderResponse getOrder(@AuthenticationPrincipal User user,
                                  @PathVariable Long id) {
        return orderService.getOrder(user.getId(), id);
    }
}
