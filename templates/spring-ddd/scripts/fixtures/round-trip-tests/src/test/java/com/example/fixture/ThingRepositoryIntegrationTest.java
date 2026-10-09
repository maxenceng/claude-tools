package com.example.fixture;

import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;

@DataJpaTest
class ThingRepositoryIntegrationTest {

    @Test
    void savesAndReadsBackWithoutClearingTheContext() {
        var saved = repository.save(fixture());
        var found = repository.findById(saved.getId());
    }
}
