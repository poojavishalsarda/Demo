package com.ibm.bookstore.service;

import com.ibm.bookstore.dto.*;
import com.ibm.bookstore.exception.BusinessException;
import com.ibm.bookstore.exception.ResourceNotFoundException;
import com.ibm.bookstore.model.Book;
import com.ibm.bookstore.model.Category;
import com.ibm.bookstore.repository.BookRepository;
import com.ibm.bookstore.repository.CategoryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

@Service
@RequiredArgsConstructor
public class BookService {

    private final BookRepository bookRepository;
    private final CategoryRepository categoryRepository;

    @Transactional(readOnly = true)
    public Page<BookResponse> search(String query, Long categoryId,
                                     BigDecimal minPrice, BigDecimal maxPrice,
                                     Pageable pageable) {
        return bookRepository.search(query, categoryId, minPrice, maxPrice, pageable)
                .map(this::toDto);
    }

    @Transactional(readOnly = true)
    public BookResponse findById(Long id) {
        return toDto(bookRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Book", id)));
    }

    @Transactional
    public BookResponse create(BookRequest req) {
        if (req.isbn() != null && bookRepository.findByIsbn(req.isbn()).isPresent()) {
            throw new BusinessException("Book with ISBN " + req.isbn() + " already exists");
        }
        Book book = buildBook(new Book(), req);
        return toDto(bookRepository.save(book));
    }

    @Transactional
    public BookResponse update(Long id, BookRequest req) {
        Book book = bookRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Book", id));
        return toDto(bookRepository.save(buildBook(book, req)));
    }

    @Transactional
    public void delete(Long id) {
        if (!bookRepository.existsById(id)) {
            throw new ResourceNotFoundException("Book", id);
        }
        bookRepository.deleteById(id);
    }

    // ── helpers ──────────────────────────────────────────────────────────────

    private Book buildBook(Book book, BookRequest req) {
        book.setTitle(req.title());
        book.setAuthor(req.author());
        book.setIsbn(req.isbn());
        book.setDescription(req.description());
        book.setPrice(req.price());
        book.setStockQuantity(req.stockQuantity());
        book.setPublisher(req.publisher());
        book.setPublicationYear(req.publicationYear());
        book.setLanguage(req.language());
        book.setPages(req.pages());
        book.setImageUrl(req.imageUrl());
        if (req.categoryId() != null) {
            Category cat = categoryRepository.findById(req.categoryId())
                    .orElseThrow(() -> new ResourceNotFoundException("Category", req.categoryId()));
            book.setCategory(cat);
        }
        return book;
    }

    BookResponse toDto(Book b) {
        return new BookResponse(
                b.getId(), b.getTitle(), b.getAuthor(), b.getIsbn(),
                b.getDescription(), b.getPrice(), b.getStockQuantity(),
                b.getPublisher(), b.getPublicationYear(), b.getLanguage(),
                b.getPages(), b.getImageUrl(),
                b.getCategory() != null ? b.getCategory().getName() : null,
                b.getCreatedAt()
        );
    }
}
