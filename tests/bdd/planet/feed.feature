@planet
Feature: Planet - Feed
  The inyoka planet is a feed aggregator. Where blogger can add their feeds and users have a single source of all blogs.


  Scenario Outline: Display the empty planet if no entries exist
    Given I am "<username>"
     When I use the "planet" and visit the "main" page
     Then I should see elements
       | item            |
       | no_planet_posts |

    Examples:
      | username  |
      | anonymous |
      | BDD-User  |


  Scenario Outline: Display a blog post if one exist
    Given I am "<username>"
      And a "blogpost" with caption "BDD-Test" exists
     When I use the "planet" and visit the "main" page
     Then I should see elements with values
       | element         | value    |
       | article_title_0 | BDD-Test |
       | article_text_0  | TEST     |

    Examples:
      | username  |
      | anonymous |
      | BDD-User  |


  Scenario Outline: Display the empty planet if only hidden items exist
    Only users with "planet.hide_entry" permission should see hidden entries
    Given I am "<username>"
      And a "blogpost" with caption "BDD-Test" is hidden
     When I use the "planet" and visit the "main" page
     Then I should see elements
       | item            |
       | no_planet_posts |

    Examples:
      | username  |
      | anonymous |
      | BDD-User  |


  Scenario Outline: Display a hidden blog post
    Given I am "<username>"
      And a "blogpost" with caption "BDD-Test" is hidden
      And I have the permission "planet.hide_entry"
     When I use the "planet" and visit the "main" page
     Then I should see elements with values
       | element         | value    |
       | article_title_0 | BDD-Test |
       | article_text_0  | TEST     |

    Examples:
      | username  |
      | anonymous |
      | BDD-User  |


  Scenario: Hide an existing blogpost
    Given I am "BDD-User"
      And I have the permission "planet.hide_entry"
      And a "blogpost" with caption "BDD-Test" exists
     When I open the "planet" in hide view
      And I click on toggle_visible_status
     Then the blogpost should be hidden


  Scenario: Restore a hidden blogpost
    Given I am "BDD-User"
      And I have the permission "planet.hide_entry"
      And a "blogpost" with caption "BDD-Test" is hidden
     When I open the "planet" in hide view
      And I click on toggle_visible_status
     Then the blogpost should be visible


  Scenario Outline: Click on cancel while hiding/restoring a blog post
    Given I am "BDD-User"
      And I have the permission "planet.hide_entry"
      And a "blogpost" with caption "BDD-Test" <entry_type>
     When I open the "planet" in hide view
      And I click on cancel
     Then the blogpost should be <expected>

    Examples:
      | entry_type | expected      |
      | exists     | visible       |
      | is hidden  | hidden by bdd |


  Scenario: Prevent hiding by anonymous
    Given I am "anonymous"
      And I have the permission "planet.hide_entry"
      And a "blogpost" with caption "BDD-Test" exists
     When I open the "planet" in hide view
     Then I should be on the login page


  Scenario: Blogpost to hide is not available
    Given I am "BDD-User"
      And I have the permission "planet.hide_entry"
     When I open the "planet" hide view of "42"
     Then I should see a "not-found" message


  Scenario: Blogpost to hide no permission
    Given I am "BDD-User"
      And a "blogpost" with caption "BDD-Test" exists
     When I open the "planet" in hide view
     Then I should see a "403" exception
