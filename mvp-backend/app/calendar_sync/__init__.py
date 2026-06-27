"""Two-way Google Calendar sync (R4 part 2).

Push the parent's owned plan entries to their Google Calendar and pull external
events back, so the plan lands where parents already live and the conflict /
coverage helpers see real commitments. Built on the R5 provider abstraction
(`app.integrations`); the daemon mirrors the R3 email-sync worker.
"""
