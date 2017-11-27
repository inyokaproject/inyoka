@planet
Feature: Planet - Blog
  This covers the blog management part from the planet.


  Scenario: Create a new blog
    Given I am "user"
      And I have the permission "planet.change_blog"
      And The user "blog_user" exits
     When I use the "planet" and visit the "blog/new" page
      And I fill out the form
      | field          | value              |
      | id_name        | BDD-Blog           |
      | id_description | blog description   |
      | id_blog_url    | http://url.invalid |
      | id_feed_url    | http://url.invalid |
      | id_active      | on                 |
      | id_user        | blog_user          |
    Then it should be successful
     And I should see elements with values
      | element        | value              |
      | id_name        | BDD-Blog           |
      | id_description | blog description   |
      | id_blog_url    | http://url.invalid |
      | id_feed_url    | http://url.invalid |
      | id_active      | on                 |
      | id_user        | blog_user          |


  Scenario: Try to create a new blog without permissions
    Given I am "user"
     When I use the "planet" and visit the "blog/new" page
     Then I should see a "403" exception

  Scenario: A blog user is required for a blog
    Given I am "user"
      And I have the permission "planet.change_blog"
     When I use the "planet" and visit the "blog/new" page
      And I fill out the form
      | field          | value              |
      | id_name        | BDD-Blog           |
      | id_description | blog description   |
      | id_blog_url    | http://url.invalid |
      | id_feed_url    | http://url.invalid |
      | id_active      | on                 |
      | id_user        | blog_user          |
     Then I should see a "user not found" field error


  Scenario Outline: URL-Fields should be validated
    Given I am "user"
      And I have the permission "planet.change_blog"
      And the user "blog_user" exits
     When I use the "planet" and visit the "blog/new" page
      And I fill out the form
        | field          | value            |
        | id_name        | BDD-Blog         |
        | id_description | blog description |
        | id_blog_url    | <blog_url>       |
        | id_feed_url    | <feed_url>       |
        | id_active      | on               |
        | id_user        | blog_user        |
     Then I should see a "invalid url" field error

    Examples:
      | blog_url        | feed_url        |
      | abc             | http://some.url |
      | a.b.c.d         | http://some.url |
      | http://some.url | a.b.c.d         |
      | http://some.url | abc             |
