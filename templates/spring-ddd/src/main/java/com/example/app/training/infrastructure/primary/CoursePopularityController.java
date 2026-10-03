package com.example.app.training.infrastructure.primary;

import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.app.training.application.CoursePopularityApplicationService;
import com.example.app.training.domain.Title;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;

@RestController
@RequestMapping("/api/courses")
class CoursePopularityController {

    private final CoursePopularityApplicationService popularities;

    CoursePopularityController(CoursePopularityApplicationService popularities) {
        this.popularities = popularities;
    }

    @GetMapping("/popularity")
    @Operation(summary = "A course's popularity, as the training catalogue vendor reports it")
    @ApiResponse(responseCode = "200", description = "The vendor has a popularity for this title")
    @ApiResponse(responseCode = "400", description = "The title is blank",
            content = @Content(schema = @Schema(implementation = ProblemDetail.class)))
    @ApiResponse(responseCode = "404", description = "The vendor has no popularity for this title yet",
            content = @Content(schema = @Schema(implementation = ProblemDetail.class)))
    @ApiResponse(responseCode = "503", description = "The vendor did not answer",
            content = @Content(schema = @Schema(implementation = ProblemDetail.class)))
    CoursePopularityResponse popularity(@RequestParam String title) {
        Title asked = new Title(title);
        return CoursePopularityResponse.from(asked, popularities.popularityOf(asked));
    }
}
