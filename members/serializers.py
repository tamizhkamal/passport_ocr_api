from rest_framework import serializers

class PassportBase64ImageSerializer(serializers.Serializer):
    image_base64 = serializers.CharField(allow_blank=False, allow_null=False, trim_whitespace=True)
