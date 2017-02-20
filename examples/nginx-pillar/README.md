Example States
==============

In the example states and pillar, there is some simply example of configuration of a nginx server where the config file for nginx is a jinja template drawing from pillar.

Based on the way Flyingcloud is called, I'm curious to know if it would be possible to allow for the targetting of pillar data when building a container. This might perhaps be done by being able to call flyingcloud with a a targetted config yaml? e.g.

        flyingcloud -c dev.yaml

If this were available as an option then it would be possible in a CI situation to programmatically target pillar data when building a container.