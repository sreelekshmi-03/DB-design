from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from app.models import User, Employer, Candidate, Job, Application
class Day14APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.candidate_user = User.objects.create_user(
            email="candidate@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )
        self.candidate, _ = Candidate.objects.get_or_create(
            user=self.candidate_user,
            defaults={"full_name": "Test Candidate"},
)
        self.employer_user = User.objects.create_user(
            email="employer@example.com",
            password="TestPass123!",
            role=User.Role.EMPLOYER,
        )
        self.employer, _ = Employer.objects.get_or_create(
            user=self.employer_user,
            defaults={"company_name":"Test Company"},
        )
        self.client.force_authenticate(user=self.candidate_user)
    def create_job(self, title, location, status=Job.Status.OPEN):
        return Job.objects.create(
            employer=self.employer,
            title=title,
            description=f"Description for {title}",
            location=location,
            status=status,
        )
    def test_job_list_only_returns_open_jobs(self):
        self.create_job("Python Developer", "Kochi")
        self.create_job("Closed Developer", "Kochi", Job.Status.CLOSED)
        response = self.client.get(reverse("job-list-create"))
        self.assertEqual(response.status_code, 200)
        titles = [job["title"] for job in response.data["results"]]
        self.assertIn("Python Developer", titles)
        self.assertNotIn("Closed Developer", titles)
    def test_job_search_filters_by_title(self):
        self.create_job("Python Developer", "Kochi")
        self.create_job("Java Developer", "Chennai")
        response = self.client.get(
            reverse("job-list-create"),
            {"search": "Python"},
        )
        self.assertEqual(response.status_code, 200)
        titles = [job["title"] for job in response.data["results"]]
        self.assertIn("Python Developer", titles)
        self.assertNotIn("Java Developer", titles)
    def test_job_location_filter(self):
        self.create_job("Python Developer", "Kochi")
        self.create_job("Backend Developer", "Chennai")
        response = self.client.get(
            reverse("job-list-create"),
            {"location": "Kochi"},
        )
        self.assertEqual(response.status_code, 200)
        titles = [job["title"] for job in response.data["results"]]
        self.assertIn("Python Developer", titles)
        self.assertNotIn("Backend Developer", titles)
    def test_job_cursor_pagination(self):
        for number in range(12):
            self.create_job(
                f"Developer {number:02d}",
                "Kochi",
            )
        response = self.client.get(reverse("job-list-create"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])
        next_response = self.client.get(response.data["next"])
        self.assertEqual(next_response.status_code, 200)
        self.assertEqual(len(next_response.data["results"]), 2)
        self.assertIsNone(next_response.data["next"])
    def test_my_applications_only_returns_current_candidates_records(self):
        job = self.create_job("Test Job", "Kochi")
        other_user = User.objects.create_user(
            email="other@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )
        another_candidate = Candidate.all_objects.filter(
            user=other_user
        ).first()
        if another_candidate is None:
            another_candidate = Candidate.all_objects.create(
                user=other_user,
                full_name="Another Candidate",
            )
        Application.objects.create(
            job=job,
            candidate=self.candidate,
        )
        another_job = self.create_job("Another Job", "Chennai")
        Application.objects.create(
            job=another_job,
            candidate=another_candidate,
        )
        response = self.client.get(reverse("application-mine"))
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["job"], job.id)
    def test_application_status_filter(self):
        job_one = self.create_job("Python Developer", "Kochi")
        job_two = self.create_job("Backend Developer", "Chennai")
        Application.objects.create(
            job=job_one,
            candidate=self.candidate,
            status=Application.Status.APPLIED,
        )
        Application.objects.create(
            job=job_two,
            candidate=self.candidate,
            status=Application.Status.SHORTLISTED,
        )
        response = self.client.get(
            reverse("application-mine"),
            {"status": Application.Status.APPLIED},
        )
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["status"],
            Application.Status.APPLIED,
        )
    def test_job_queryset_uses_select_related(self):
        self.create_job("Python Developer", "Kochi")
        queryset = Job.objects.filter(
            status=Job.Status.OPEN
        ).select_related("employer", "employer__user")
        sql = str(queryset.query).upper()
        self.assertIn("JOIN", sql)
        self.assertIn("EMPLOYER", sql)

class Day16EmployerJobAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.employer_user = User.objects.create_user(
            email="employer16@example.com",
            password="TestPass123!",
            role=User.Role.EMPLOYER,
        )
        self.employer, _ = Employer.objects.get_or_create(
            user=self.employer_user,
            defaults={"company_name": "Employer One"},
        )

        self.other_employer_user = User.objects.create_user(
            email="employer_two16@example.com",
            password="TestPass123!",
            role=User.Role.EMPLOYER,
        )
        self.other_employer, _ = Employer.objects.get_or_create(
            user=self.other_employer_user,
            defaults={"company_name": "Employer Two"},
        )

        self.candidate_user = User.objects.create_user(
            email="candidate16@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )
        Candidate.objects.get_or_create(
            user=self.candidate_user,
            defaults={"full_name": "Test Candidate"},
        )

    def create_job(self, employer=None, **overrides):
        data = {
            "title": "Python Developer",
            "description": "Build Python applications.",
            "location": "Kochi",
            "status": Job.Status.DRAFT,
        }
        data.update(overrides)
        return Job.objects.create(
            employer=employer or self.employer,
            **data,
        )

    def test_employer_can_create_job(self):
        self.client.force_authenticate(user=self.employer_user)

        response = self.client.post(
            reverse("job-list-create"),
            {
                "title": "Backend Developer",
                "description": "Develop APIs.",
                "location": "Kochi",
                "salary_min": 30000,
                "salary_max": 60000,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Job.objects.get(id=response.data["id"]).employer,
            self.employer,
        )

    def test_candidate_cannot_create_job(self):
        self.client.force_authenticate(user=self.candidate_user)

        response = self.client.post(
            reverse("job-list-create"),
            {
                "title": "Backend Developer",
                "description": "Develop APIs.",
                "location": "Kochi",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Job.objects.filter(title="Backend Developer").exists()
        )

    def test_employer_cannot_access_another_employers_job(self):
        job = self.create_job(employer=self.other_employer)
        self.client.force_authenticate(user=self.employer_user)

        response = self.client.get(
            reverse("job-detail", kwargs={"pk": job.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_employer_cannot_edit_another_employers_job(self):
        job = self.create_job(employer=self.other_employer)
        self.client.force_authenticate(user=self.employer_user)

        response = self.client.patch(
            reverse("job-detail", kwargs={"pk": job.pk}),
            {"title": "Hijacked title"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        job.refresh_from_db()
        self.assertEqual(job.title, "Python Developer")

    def test_invalid_salary_range_is_rejected(self):
        self.client.force_authenticate(user=self.employer_user)

        response = self.client.post(
            reverse("job-list-create"),
            {
                "title": "Salary Test",
                "description": "Test salary validation.",
                "location": "Kochi",
                "salary_min": 80000,
                "salary_max": 40000,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("salary_max", response.data["errors"])
    def test_employer_can_activate_and_deactivate_job(self):
        job = self.create_job()
        self.client.force_authenticate(user=self.employer_user)
        url = reverse("job-detail", kwargs={"pk": job.pk})

        activate_response = self.client.patch(
            url,
            {"status": Job.Status.OPEN},
            format="json",
        )
        self.assertEqual(activate_response.status_code, 200)

        job.refresh_from_db()
        self.assertEqual(job.status, Job.Status.OPEN)

        deactivate_response = self.client.patch(
            url,
            {"status": Job.Status.CLOSED},
            format="json",
        )
        self.assertEqual(deactivate_response.status_code, 200)

        job.refresh_from_db()
        self.assertEqual(job.status, Job.Status.CLOSED)

    def test_employer_job_list_includes_own_draft_and_closed_jobs(self):
        draft_job = self.create_job(title="Draft Job")
        closed_job = self.create_job(
            title="Closed Job",
            status=Job.Status.CLOSED,
        )
        self.create_job(
            employer=self.other_employer,
            title="Other Employer Job",
        )

        self.client.force_authenticate(user=self.employer_user)
        response = self.client.get(reverse("employer-job-list"))

        self.assertEqual(response.status_code, 200)
        results = response.data.get("results", response.data)
        returned_ids = {item["id"] for item in results}

        self.assertIn(draft_job.id, returned_ids)
        self.assertIn(closed_job.id, returned_ids)
        self.assertNotIn(
            Job.objects.get(title="Other Employer Job").id,
            returned_ids,
        )
