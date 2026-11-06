package com.ibm.bookstore.dto;

public record AuthResponse(String accessToken, String tokenType, Long expiresIn) {

    public AuthResponse(String accessToken, Long expiresIn) {
        this(accessToken, "Bearer", expiresIn);
    }
}
