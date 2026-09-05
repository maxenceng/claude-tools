package com.example.app.training.domain;

/**
 * Fills a course's popularity from the training catalogue vendor, once. See ADR 0009 for why
 * this — not a controller or a repository — is where the outbound-client lookup is called from.
 */
public record CourseManager(CourseCataloguePort catalogue) {

    /**
     * The same course, with its popularity filled where the vendor has one and the course does
     * not yet. Already-present popularity is never looked up again — this manager does not
     * decide that on its own; it is simply never asked a second time (nothing here tracks that,
     * unlike RAWG's duration lookup, since this example has no re-run loop to guard).
     */
    public Course fillPopularity(Course course) {
        if (course.popularity().isPresent()) {
            return course;
        }

        return catalogue.lookup(course.title()).map(course::withPopularity).orElse(course);
    }
}
