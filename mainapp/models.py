from django.db import models


class UserProfile(models.Model):
    region = models.ForeignKey(to='RegionModel', on_delete=models.CASCADE, null=True)
    district = models.ForeignKey(to='DistrictModel', on_delete=models.CASCADE, null=True)
    gathering = models.ForeignKey(to='GatheringModel', on_delete=models.CASCADE, null=True)
    event_location = models.ForeignKey(to='EventLocationModel', on_delete=models.CASCADE, null=True)

    external_id = models.PositiveIntegerField(
        verbose_name='ID пользователя',
        unique=True,
        null=True,
    )

    name = models.CharField(
        max_length=64,
        verbose_name='Имя пользователя',
    )

    def __str__(self):
        return f'{self.external_id} {self.name}'

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'


class RegionModel(models.Model):
    name = models.CharField(max_length=128)
    origin_id = models.IntegerField()

    class Meta:
        verbose_name = 'Область'
        verbose_name_plural = 'Области'

    def __str__(self):
        return f'{self.name} {self.pk}'


class DistrictModel(models.Model):
    name = models.CharField(max_length=128)
    origin_id = models.IntegerField()
    region = models.ForeignKey(
        to='RegionModel',
        on_delete=models.CASCADE,
        related_name='districts',
        verbose_name='tuman',
    )

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

    def __str__(self):
        return f'{self.name} {self.pk}'


class GatheringModel(models.Model):
    name = models.CharField(max_length=128)
    origin_id = models.IntegerField()
    district = models.ForeignKey(
        to='DistrictModel',
        on_delete=models.CASCADE,
        related_name='gatherings',
        verbose_name='mahalla',
    )

    class Meta:
        verbose_name = 'Район'
        verbose_name_plural = 'Районы'

    def __str__(self):
        return f'{self.name} {self.pk}'


class EventLocationModel(models.Model):
    name = models.CharField(max_length=256)
    origin_id = models.IntegerField()
    gathering = models.ForeignKey(
        to='GatheringModel',
        on_delete=models.CASCADE,
        related_name='event_location',
    )

    def __str__(self):
        return f'{self.name} {self.pk}'


class Register(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    event_location = models.ForeignKey(
        to='EventLocationModel',
        on_delete=models.CASCADE,
        related_name='register',
    )
    lat = models.FloatField(null=True)
    long = models.FloatField(null=True)

    class Meta:
        verbose_name = 'Регистр'
        verbose_name_plural = 'Регистр'

    def __str__(self):
        return f'{self.user} {self.pk}'
