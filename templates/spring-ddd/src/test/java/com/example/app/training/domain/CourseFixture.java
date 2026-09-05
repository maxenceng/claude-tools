package com.example.app.training.domain;

import static com.example.app.training.domain.CourseIdFixture.courseId;
import static com.example.app.training.domain.PopularityFixture.popularity;
import static com.example.app.training.domain.TitleFixture.title;

public final class CourseFixture {

    private CourseFixture() {
    }

    public static Course.CourseBuilder courseBuilder() {
        return Course.builder().id(courseId()).title(title());
    }

    public static Course course() {
        return courseBuilder().build();
    }

    public static Course courseWithPopularity() {
        return courseBuilder().popularity(popularity()).build();
    }
}
