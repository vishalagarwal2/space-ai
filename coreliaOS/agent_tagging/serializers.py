from rest_framework import serializers
from .models import CreateGroupModel

class GetGroupSerializer(serializers.Serializer):
    grp_id = serializers.UUIDField(required=True)

    def validate_grp_id(self, value):
        """
        Validate that the group with the given grp_id exists and belongs to the authenticated user.
        """
        user = self.context['request'].user
        try:
            group = CreateGroupModel.objects.get(grp_id=value, user=user)
        except CreateGroupModel.DoesNotExist:
            raise serializers.ValidationError(f"Group with grp_id {value} not found or does not belong to the user")
        return value

    def get_group_data(self):
        """
        Return the group data in the specified format.
        """
        group = CreateGroupModel.objects.get(grp_id=self.validated_data['grp_id'], user=self.context['request'].user)
        return {
            'grp_id': str(group.grp_id),
            'name': group.name,
            'agents': group.agent_labels
        }
