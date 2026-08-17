# done

1. Confirm the work is merged. If it is not, say so and stop. Check before anything else:
   the rest of this step writes a record of what landed, and nothing has landed yet.
2. Set `status: done`.
3. Fill in *Notes* with anything the code will not show — an approach rejected, a
   constraint found. Skip it if there is genuinely nothing; padding trains people to stop
   reading the section.
4. Invoke the `project-retro` skill if anything during the ticket was done by hand more
   than twice, or if the same correction came up repeatedly.
5. Raise an ADR if a decision was made that someone could reasonably reverse later
   without knowing why it was taken. An ADR already written during the ticket counts —
   check before writing a second description of the same decision.
