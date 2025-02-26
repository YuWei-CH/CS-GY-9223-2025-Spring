### LF2 Trigger Solution
We have set up an SQS trigger in AWS. if a task enters the queue, LF2 is set off to process the task. also, on request, we have set up a scheduler to call LF2 every 1 minute to process the contents of the queue. To enhance the robustness of the code, we have added the following logic:
1. If there is no “Records” in the event, it means the queue is empty, so it will return a status 200 and state that the queue is currently empty.

2. If there are “Records” in the event, it means that LF2 needs to be triggered to process the task in the queue.