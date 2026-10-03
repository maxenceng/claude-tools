package com.example.app.training.infrastructure.primary;

import com.example.app.training.domain.Popularity;
import com.example.app.training.domain.Title;

import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.media.Schema.RequiredMode;

record CoursePopularityResponse(
        @Schema(requiredMode = RequiredMode.REQUIRED) String title,
        @Schema(requiredMode = RequiredMode.REQUIRED) int popularity) {

    static CoursePopularityResponse from(Title title, Popularity popularity) {
        return new CoursePopularityResponse(title.value(), popularity.value());
    }
}
