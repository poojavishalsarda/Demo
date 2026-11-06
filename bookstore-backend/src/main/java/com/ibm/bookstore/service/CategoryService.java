package com.ibm.bookstore.service;

import com.ibm.bookstore.dto.CategoryRequest;
import com.ibm.bookstore.dto.CategoryResponse;
import com.ibm.bookstore.exception.BusinessException;
import com.ibm.bookstore.exception.ResourceNotFoundException;
import com.ibm.bookstore.model.Category;
import com.ibm.bookstore.repository.CategoryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class CategoryService {

    private final CategoryRepository categoryRepository;

    @Transactional(readOnly = true)
    public List<CategoryResponse> findAll() {
        return categoryRepository.findAll().stream().map(this::toDto).toList();
    }

    @Transactional(readOnly = true)
    public CategoryResponse findById(Long id) {
        return toDto(categoryRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Category", id)));
    }

    @Transactional
    public CategoryResponse create(CategoryRequest req) {
        if (categoryRepository.existsByNameIgnoreCase(req.name())) {
            throw new BusinessException("Category already exists: " + req.name());
        }
        Category cat = Category.builder().name(req.name()).description(req.description()).build();
        return toDto(categoryRepository.save(cat));
    }

    @Transactional
    public CategoryResponse update(Long id, CategoryRequest req) {
        Category cat = categoryRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Category", id));
        cat.setName(req.name());
        cat.setDescription(req.description());
        return toDto(categoryRepository.save(cat));
    }

    @Transactional
    public void delete(Long id) {
        if (!categoryRepository.existsById(id)) {
            throw new ResourceNotFoundException("Category", id);
        }
        categoryRepository.deleteById(id);
    }

    private CategoryResponse toDto(Category c) {
        return new CategoryResponse(c.getId(), c.getName(), c.getDescription());
    }
}
