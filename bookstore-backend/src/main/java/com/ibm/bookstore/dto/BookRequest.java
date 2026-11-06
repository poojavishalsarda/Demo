package com.ibm.bookstore.dto;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;

public record BookRequest(
        @NotBlank String title,
        @NotBlank String author,
        String isbn,
        String description,
        @NotNull @DecimalMin("0.01") BigDecimal price,
        @NotNull @Min(0) Integer stockQuantity,
        String publisher,
        Integer publicationYear,
        String language,
        Integer pages,
        String imageUrl,
        Long categoryId
) {}
