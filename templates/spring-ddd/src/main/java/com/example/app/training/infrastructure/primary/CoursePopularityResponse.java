package com.example.app.training.infrastructure.primary;

import com.example.app.training.domain.Popularity;
import com.example.app.training.domain.Title;

record CoursePopularityResponse(String title, int popularity) {

    static CoursePopularityResponse from(Title title, Popularity popularity) {
        return new CoursePopularityResponse(title.value(), popularity.value());
    }
}
