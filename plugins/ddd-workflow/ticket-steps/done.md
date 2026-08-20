# done

1. Confirm the work is merged. If it is not, say so and stop. Check before anything else:
   the rest of this step writes a record of what landed, and nothing has landed yet.
2. Set `status: done`. Closing a ticket writes files, so it lands on a branch and a PR
   like any other change — `start` said this and the habit does not survive a step that
   does not repeat it.
3. Fill in *Notes* with anything the code will not show — an approach rejected, a
   constraint found. Skip it if there is genuinely nothing; padding trains people to stop
   reading the section.
4. Invoke the `project-retro` skill if anything during the ticket was done by hand more
   than twice, or if the same correction came up repeatedly.
5. Raise an ADR if a decision was made that someone could reasonably reverse later
   without knowing why it was taken. An ADR already written during the ticket counts —
   check before writing a second description of the same decision.

   Read *Model decision* against the code before deciding there is nothing to write. If
   review reversed the modelling, that section now argues for a shape the code does not
   have, and it is the first thing the next person reads. Leave it as written — it is the
   record of what was decided — and write the ADR that supersedes it. A ticket whose
   *Model decision* contradicts the code, with nothing pointing anywhere else, is how a
   settled question gets reopened by someone who thinks they have found a bug.
