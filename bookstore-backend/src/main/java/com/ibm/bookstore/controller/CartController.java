package com.ibm.bookstore.controller;

import com.ibm.bookstore.dto.*;
import com.ibm.bookstore.model.User;
import com.ibm.bookstore.service.CartService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/cart")
@RequiredArgsConstructor
public class CartController {

    private final CartService cartService;

    /** GET /api/v1/cart */
    @GetMapping
    public CartResponse getCart(@AuthenticationPrincipal User user) {
        return cartService.getCart(user.getId());
    }

    /** POST /api/v1/cart/items */
    @PostMapping("/items")
    @ResponseStatus(HttpStatus.CREATED)
    public CartResponse addItem(@AuthenticationPrincipal User user,
                                @Valid @RequestBody CartItemRequest request) {
        return cartService.addItem(user.getId(), request);
    }

    /** PUT /api/v1/cart/items/{bookId}?quantity=3 */
    @PutMapping("/items/{bookId}")
    public CartResponse updateItem(@AuthenticationPrincipal User user,
                                   @PathVariable Long bookId,
                                   @RequestParam int quantity) {
        return cartService.updateItem(user.getId(), bookId, quantity);
    }

    /** DELETE /api/v1/cart/items/{bookId} */
    @DeleteMapping("/items/{bookId}")
    public CartResponse removeItem(@AuthenticationPrincipal User user,
                                   @PathVariable Long bookId) {
        return cartService.removeItem(user.getId(), bookId);
    }

    /** DELETE /api/v1/cart */
    @DeleteMapping
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void clearCart(@AuthenticationPrincipal User user) {
        cartService.clearCart(user.getId());
    }
}
