package com.example.app.training.domain;

import java.util.UUID;

public final class CourseIdFixture {

    private CourseIdFixture() {
    }

    public static CourseId courseId() {
        return new CourseId(UUID.fromString("11111111-1111-1111-1111-111111111111"));
    }
}
