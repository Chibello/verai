# serializers.py
from rest_framework import serializers
from .models import BankDetails

class BankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetails
        fields = ['account_number', 'bank_code', 'bank_name']

    def create(self, validated_data):
        user = self.context['request'].user
        return BankDetails.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        instance.account_number = validated_data.get('account_number', instance.account_number)
        instance.bank_code = validated_data.get('bank_code', instance.bank_code)
        instance.bank_name = validated_data.get('bank_name', instance.bank_name)
        instance.save()
        return instance
