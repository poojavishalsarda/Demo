package com.ibm.bookstore.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record BookResponse(
        Long id,
        String title,
        String author,
        String isbn,
        String description,
        BigDecimal price,
        Integer stockQuantity,
        String publisher,
        Integer publicationYear,
        String language,
        Integer pages,
        String imageUrl,
        String categoryName,
        LocalDateTime createdAt
) {}
