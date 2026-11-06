package com.ibm.bookstore.dto;

import com.ibm.bookstore.model.OrderStatus;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

public record OrderResponse(
        Long id,
        OrderStatus status,
        BigDecimal totalAmount,
        String shippingAddress,
        String shippingCity,
        String shippingCountry,
        String shippingPostalCode,
        List<OrderItemResponse> items,
        LocalDateTime createdAt
) {}
