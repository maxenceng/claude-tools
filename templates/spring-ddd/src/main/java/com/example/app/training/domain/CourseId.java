package com.example.app.training.domain;

import java.util.UUID;

import com.example.app.error.domain.Assert;

/** What identifies a course. */
public record CourseId(UUID value) {

    public CourseId {
        Assert.notNull("courseId", value);
    }
}
