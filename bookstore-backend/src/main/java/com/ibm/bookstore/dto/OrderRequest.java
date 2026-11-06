package com.ibm.bookstore.dto;

import jakarta.validation.constraints.NotBlank;

public record OrderRequest(
        @NotBlank String shippingAddress,
        @NotBlank String shippingCity,
        @NotBlank String shippingCountry,
        @NotBlank String shippingPostalCode
) {}
