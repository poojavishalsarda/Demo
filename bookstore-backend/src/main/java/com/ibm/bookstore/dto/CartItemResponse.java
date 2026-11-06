package com.ibm.bookstore.dto;

import java.math.BigDecimal;

public record CartItemResponse(
        Long cartItemId,
        Long bookId,
        String bookTitle,
        String bookAuthor,
        String imageUrl,
        BigDecimal unitPrice,
        Integer quantity,
        BigDecimal subTotal
) {}
