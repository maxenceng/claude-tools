package com.example.app.training.infrastructure.primary;

import static com.example.app.training.domain.PopularityFixture.popularity;
import static com.example.app.training.domain.TitleFixture.title;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.example.app.training.application.CoursePopularityApplicationService;
import com.example.app.training.domain.PopularityNotFoundException;
import com.example.app.training.infrastructure.secondary.client.CourseCatalogueUnreachableException;

@WebMvcTest(CoursePopularityController.class)
class CoursePopularityControllerTest {

    @Autowired
    private MockMvc mvc;

    @MockitoBean
    private CoursePopularityApplicationService service;

    @Test
    void shouldAnswerThePopularity() throws Exception {
        when(service.popularityOf(title())).thenReturn(popularity());

        mvc.perform(get("/api/courses/popularity").param("title", title().value()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value(title().value()))
                .andExpect(jsonPath("$.popularity").value(popularity().value()));
    }

    @Test
    void shouldRefuseABlankTitle() throws Exception {
        mvc.perform(get("/api/courses/popularity").param("title", " "))
                .andExpect(status().isBadRequest());
    }

    @Test
    void shouldAnswerNotFoundWhereThereIsNoPopularity() throws Exception {
        when(service.popularityOf(title())).thenThrow(new PopularityNotFoundException(title()));

        mvc.perform(get("/api/courses/popularity").param("title", title().value()))
                .andExpect(status().isNotFound());
    }

    @Test
    void shouldAnswerUnavailableWhereTheCatalogueIsUnreachable() throws Exception {
        when(service.popularityOf(title())).thenThrow(new CourseCatalogueUnreachableException("GET https://api.example/api/courses refused: HTTP 500"));

        mvc.perform(get("/api/courses/popularity").param("title", title().value()))
                .andExpect(status().isServiceUnavailable())
                .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
                .andExpect(jsonPath("$.detail").value("The training catalogue did not answer; try again later."));
    }
}
