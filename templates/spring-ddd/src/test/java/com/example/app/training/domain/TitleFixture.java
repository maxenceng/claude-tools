package com.example.app.training.domain;

public final class TitleFixture {

    private TitleFixture() {
    }

    public static Title title() {
        return new Title("Introduction to Hexagonal Architecture");
    }
}
