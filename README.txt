Thank you for downloading Assignment Collector/Grader!

Installation instructions for both developers and server administrators are in INSTALL.txt.

The changelog can be found in CHANGELOG.txt.

The latest version release notes:
-------------------------------------------------------------------------------
Version 2.0 Release - 3/24/2012
===============================================================================
Phew! 2.0 has been a long time coming. The biggest feature of this release is
an improved admin experience. Now admins can only view and edit courses and 
assignments that they created. Superusers are exempt from this constraint.
This compartmentalization has been 2 years in the making and should improve the
multi-user capabilities of ACG.
The grader has also been completely overhauled and moved into its own app. This
allows us to support more languages in the future. Grading should be faster now
too. The grader has been re-written to be cleaner and easier to understand and
extend.
The tie-ins for a plagiarism detection system have been placed, but currently
are unimplemented. Selecting plagiarism detection in the admin interface does 
nothing for now.
ACG now has the option of sending the grader results to students via email in
addition to viewing the results on the site. This hopefully reduces load on the
server in addition to providing students with another useful tool. This feature
can be enabled and configured in the settings, and by default does not send any
emails.
In Summary:
*   Admins can only edit their own Courses and Assignments.
*	The grader is more stable and faster than before.
*	Students can have their results emailed to them.
*	Generated gradesheets are a little prettier.
*	Hooks for future implementation of plagiarism detection are in place.
*	General bug fixes and minor improvements.
