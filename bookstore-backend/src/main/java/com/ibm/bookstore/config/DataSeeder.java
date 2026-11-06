package com.ibm.bookstore.config;

import com.ibm.bookstore.model.*;
import com.ibm.bookstore.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.math.BigDecimal;

@Configuration
@RequiredArgsConstructor
@Slf4j
public class DataSeeder {

    private final CategoryRepository categoryRepository;
    private final BookRepository      bookRepository;
    private final UserRepository      userRepository;
    private final CartRepository      cartRepository;
    private final PasswordEncoder     passwordEncoder;

    /**
     * Seeds demo data only in the default (dev) profile.
     * Not loaded when spring.profiles.active=prod.
     */
    @Bean
    @Profile("!prod")
    CommandLineRunner seedDatabase() {
        return args -> {
            if (categoryRepository.count() > 0) return;

            // Categories
            Category fiction = categoryRepository.save(
                    Category.builder().name("Fiction").description("Fictional literature").build());
            Category tech = categoryRepository.save(
                    Category.builder().name("Technology").description("Software and tech books").build());
            Category science = categoryRepository.save(
                    Category.builder().name("Science").description("Scientific publications").build());

            // Books
            bookRepository.save(Book.builder()
                    .title("Clean Code").author("Robert C. Martin").isbn("9780132350884")
                    .description("A handbook of agile software craftsmanship.")
                    .price(new BigDecimal("34.99")).stockQuantity(50)
                    .publisher("Prentice Hall").publicationYear(2008)
                    .language("English").pages(431).category(tech).build());

            bookRepository.save(Book.builder()
                    .title("The Pragmatic Programmer").author("David Thomas, Andrew Hunt").isbn("9780135957059")
                    .description("Your journey to mastery, 20th Anniversary Edition.")
                    .price(new BigDecimal("44.99")).stockQuantity(35)
                    .publisher("Addison-Wesley").publicationYear(2019)
                    .language("English").pages(352).category(tech).build());

            bookRepository.save(Book.builder()
                    .title("Design Patterns").author("Gang of Four").isbn("9780201633610")
                    .description("Elements of reusable object-oriented software.")
                    .price(new BigDecimal("49.99")).stockQuantity(20)
                    .publisher("Addison-Wesley").publicationYear(1994)
                    .language("English").pages(395).category(tech).build());

            bookRepository.save(Book.builder()
                    .title("A Brief History of Time").author("Stephen Hawking").isbn("9780553380163")
                    .description("From the Big Bang to Black Holes.")
                    .price(new BigDecimal("14.99")).stockQuantity(60)
                    .publisher("Bantam Books").publicationYear(1988)
                    .language("English").pages(212).category(science).build());

            bookRepository.save(Book.builder()
                    .title("1984").author("George Orwell").isbn("9780451524935")
                    .description("Dystopian social science fiction novel.")
                    .price(new BigDecimal("12.99")).stockQuantity(100)
                    .publisher("Signet Classic").publicationYear(1949)
                    .language("English").pages(328).category(fiction).build());

            // Admin user — password is read from env in production
            User admin = User.builder()
                    .firstName("Admin").lastName("User")
                    .email("admin@bookstore.ibm.com")
                    .password(passwordEncoder.encode("Admin@SecurePass123"))
                    .role(Role.ROLE_ADMIN).build();
            admin = userRepository.save(admin);
            cartRepository.save(Cart.builder().user(admin).build());

            log.info("Demo data seeded successfully.");
        };
    }
}
