package com.example.app.training.application;

import org.springframework.stereotype.Service;

import com.example.app.training.domain.CourseCataloguePort;
import com.example.app.training.domain.CourseManager;
import com.example.app.training.domain.Popularity;
import com.example.app.training.domain.Title;

@Service
public class CoursePopularityApplicationService {

    private final CourseManager manager;

    public CoursePopularityApplicationService(CourseCataloguePort catalogue) {
        this.manager = new CourseManager(catalogue);
    }

    public Popularity popularityOf(Title title) {
        return manager.popularityOf(title);
    }
}
