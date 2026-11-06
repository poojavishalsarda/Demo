package com.ibm.bookstore.dto;

import com.ibm.bookstore.model.Role;

public record UserResponse(Long id, String firstName, String lastName, String email, String phone, Role role) {}
