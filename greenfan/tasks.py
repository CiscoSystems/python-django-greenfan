from greenfan.models import Job

from celery import task

@task
def run(job_id):
    job = Job.objects.get(pk=job_id)
    try:
        job.next_step()
    except StopIteration:
        return
    run.delay(job_id)
