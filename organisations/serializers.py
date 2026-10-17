from rest_framework import serializers

from organisations.models import OrganisationMembership


class OrganisationMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationMembership
        fields = [
            "id",
            "organisation",
            "user",
            "role",
            "created_at",
        ]
        # Not strictly necessary as this serializer will only be used for GET
        # but good for consistency.
        read_only_fields = fields


class OrganisationMembershipCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationMembership
        fields = [
            "id",
            "user",
            "role",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

    # DRF convention - validation of the field called user that is
    # being sent in the request is done automatically with this
    # function.
    # Since the user is a FK to Org membership, the passed object
    # is the actual user object.
    def validate_user(self, value):
        # Usual context is just the request, view, format. But now we
        # have added the organisation from the URL as context
        # so that we can check if the user is already a member of the
        # organisation we are working on.
        organisation = self.context["organisation"]

        if OrganisationMembership.objects.filter(
            organisation=organisation,
            user=value,
        ).exists():
            raise serializers.ValidationError(
                "This user is already a member of the organisation."
            )

        return value


class OrganisationMembershipUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationMembership
        fields = [
            "id",
            "organisation",
            "user",
            "role",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "organisation",
            "user",
            "created_at",
        ]

    # Important to remember: The serializers have self.instance as the old value
    # since the view they are used in corresponds to a URL containing a UUID. So
    # behind the scenes the serializer is initialised with the corresponding
    # object model as the instance, so that it can be validated against
    # the new data.
    # Check the view that uses this class for more info.

    def validate_role(self, value):
        # Just a failsafe to avoid crashes when accessing self.instance.role
        if self.instance is None:
            return value

        is_currently_administrator = (
            self.instance.role == OrganisationMembership.Role.ADMINISTRATOR
        )

        is_being_demoted = value != OrganisationMembership.Role.ADMINISTRATOR

        if is_currently_administrator and is_being_demoted:
            administrator_count = OrganisationMembership.objects.filter(
                organisation=self.instance.organisation,
                role=OrganisationMembership.Role.ADMINISTRATOR,
            ).count()

            if administrator_count <= 1:
                raise serializers.ValidationError(
                    "An organisation must have at least one administrator."
                )

        return value
