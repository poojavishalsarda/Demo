package com.ibm.bookstore.controller;

import com.ibm.bookstore.dto.OrderResponse;
import com.ibm.bookstore.model.OrderStatus;
import com.ibm.bookstore.service.OrderService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/admin/orders")
@RequiredArgsConstructor
public class AdminOrderController {

    private final OrderService orderService;

    /** GET /api/v1/admin/orders  (ADMIN) */
    @GetMapping
    public Page<OrderResponse> getAllOrders(Pageable pageable) {
        return orderService.getAllOrders(pageable);
    }

    /** PATCH /api/v1/admin/orders/{id}/status?status=SHIPPED  (ADMIN) */
    @PatchMapping("/{id}/status")
    public OrderResponse updateStatus(@PathVariable Long id,
                                      @RequestParam OrderStatus status) {
        return orderService.updateStatus(id, status);
    }
}
