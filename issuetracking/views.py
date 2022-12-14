from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from .permissions import IsContributor, IsProjectOwner, IsIssueOwner, IsCommentOwner
from django.shortcuts import get_object_or_404


from .models import User, Project, Contributor, Issue, Comment
from .serializers import ProjectListSerializer, ProjectDetailSerializer
from .serializers import (
    ProjectIssueSerializer,
    CommentSerializer,
)
from .serializers import UserSignupSerializer
from .serializers import ContributorSerializer


class UserSignupViewset(ModelViewSet):
    http_method_names = ["post"]
    serializer_class = UserSignupSerializer


class UserViewset(ModelViewSet):
    http_method_names = ["get"]
    serializer_class = UserSignupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action == "list":
            return User.objects.filter(username=self.request.user)
        raise ValidationError(detail="This url is not an endpoint")


class ProjectViewset(ModelViewSet):

    http_method_names = ["post", "get", "put", "delete"]
    serializer_class = ProjectListSerializer
    permission_classes = [IsAuthenticated]
    owner_permission_classes = [IsAuthenticated(), IsProjectOwner()]
    contributor_permission_classes = [IsAuthenticated(), IsContributor()]

    def get_queryset(self):
        if self.action == "retrieve":
            project_id = self.kwargs["pk"]
            return Project.objects.filter(id=project_id)
        return Project.objects.filter(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ["retrieve"]:
            return ProjectDetailSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ["destroy", "update"]:
            return self.owner_permission_classes
        if self.action in ["retrieve"]:
            return self.contributor_permission_classes
        return super().get_permissions()


class ProjectContributorViewset(ModelViewSet):

    http_method_names = ["post", "get", "delete"]
    serializer_class = ContributorSerializer
    permission_classes = [IsAuthenticated, IsContributor]
    owner_permission_classes = [IsAuthenticated(), IsProjectOwner()]

    def get_queryset(self):
        return Contributor.objects.filter(project=self.kwargs["project_pk"])

    def get_permissions(self):
        if self.action in ["retrieve", "update"]:
            raise ValidationError("only the delete method is allowed on this url")
        if self.action in ["create", "update"]:
            return self.owner_permission_classes
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        contributor = get_object_or_404(
            Contributor, user=self.kwargs["pk"], project=self.kwargs["project_pk"]
        )
        if contributor.role == "collaborator":
            self.kwargs["pk"] = contributor.id
            return super().destroy(self, request, *args, **kwargs)
        raise ValidationError(detail="The author of the project cannot be deleted")


class ProjectIssueViewset(ModelViewSet):

    http_method_names = ["post", "get", "put", "delete"]
    serializer_class = ProjectIssueSerializer
    permission_classes = [IsAuthenticated, IsContributor]
    owner_permission_classes = [IsAuthenticated(), IsIssueOwner()]

    def get_queryset(self):
        return Issue.objects.filter(project=self.kwargs["project_pk"])

    def get_permissions(self):

        if self.action == "retrieve":
            raise ValidationError("get method are not allowed on this url")

        if self.action in ["update", "destroy"]:
            return self.owner_permission_classes
        return super().get_permissions()


class CommentViewset(ModelViewSet):

    http_method_names = ["post", "get", "put", "delete"]
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsContributor]
    owner_permission_classes = [IsAuthenticated(), IsCommentOwner()]

    def get_queryset(self):
        return Comment.objects.filter(issue=self.kwargs["issue_pk"])

    def get_permissions(self):
        # test if issue match with project
        get_object_or_404(
            Issue, id=self.kwargs["issue_pk"], project=self.kwargs["project_pk"]
        )
        # test if comment match with issue
        if self.action in ["update", "destroy", "retrieve"]:
            get_object_or_404(
                Comment, id=self.kwargs["pk"], issue=self.kwargs["issue_pk"]
            )
        if self.action in ["update", "destroy"]:
            return self.owner_permission_classes
        return super().get_permissions()
