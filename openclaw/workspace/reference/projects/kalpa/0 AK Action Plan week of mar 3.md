##Things to focus on:
- ci (automation, plan almost done)
- dev ops optimization with claude help - what should we be thinking about what should we be focused on
	- logging?
	- cloudwatch?
	
Listed as ITEM 3

---
	
- env and SSM - lets be intelligent about how we set this transition up

NOT YET SCOPED, NEED ENV Variable.

---

- sync repos to VMs (add staging VM so this is feature complete?)
- CD green/blue, docker, ECS setup, actions, staging VM etc. (/kalpa-docs/operations/wellmed-cd-plan)

Listed as ITEM 4

Team identified a problem with port/refactor code. Seems to stem from porting db over from laravel framework as is with very little changes, need to explore. 
	- PROPS usage (Json file convert to string and convert back in BFF)
	- Create/Update framework does not exist in go (we have setup GORM)
	- Need to understand POSTMAN and how it is created from code (automatically), body is showing detail with several redundant layers
	- props (used in this case originally to avoid joins, speed up performance) for this use case is unnecessary now that we have Elastic Search and redis running
	- need to deterimine how to use ai to look end to end DB -> Go code -> Postman
	
Listed as ITEM 1

- separate Consultation from Backbone
- EMR (My strong preference is to have this be a structured model. and storage should reflect FHIR standards in JSON)

LISTED AS ITEM 2

##Pending not yet addressed.
- migration -> EMR - I would like to build an emr scrapper this week (this feature is my side project for the team) -> this gets us to uploading visits as well
- ai supported reporting tool concept (ES has a list of vectors, ai queries can combine these or create a request to dev, with pre-populated job design, cost (time/frequency estimate), we should mock this up and then dogfood it for several reports we need.

- application level logging - should we define a strategy for this, that way ai can help us implement? want to capture the things that truly help us debug and not just dumbly push a million lines a day to cloud watch. Let's bias toward things that are more often to fail and then otherwise leave threads that we can pull later, as required.
- buildout next steps from test strategy after we get wellmed plus go running.

##Completed:
- update questions.md - prompt claude to look at entire repo and surface questions of a similar nature (deviation from best practice, hanging slop, poorly written code, poorly designed structure)
	- seems #3.1 has already been addressed..?
	- I believe the gateway api client feature added several handling elements including rate limiting with exponential back off - need to confirm.