package com.ibm.bookstore.dto;

import java.math.BigDecimal;

public record OrderItemResponse(
        Long bookId,
        String bookTitle,
        Integer quantity,
        BigDecimal unitPrice,
        BigDecimal subTotal
) {}
