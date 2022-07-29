import datetime
from django.utils import timezone
from moc.models import MoCMonth, MoCYear
from hul import constants


class CreateMoC(object):

    @staticmethod
    def create_moc_year(year):
        moc_year = MoCYear()
        moc_year.year = year
        moc_year.save()
        # CreateMoC.create_moc_month(moc_year)

    @staticmethod
    def create_moc_month(year):
        moc_months = []
        for month in constants.MONTHS:
            moc_month = {
                'moc_year': year
            }
            if month % 12 == 0:
                moc_month.update({
                    'start_date': timezone.datetime.date(datetime.datetime(year.year - 1, month, constants.MOC_START_DATE)),
                    'end_date': timezone.datetime.date(datetime.datetime(year.year, 1, constants.MOC_END_DATE)),
                    'name': 'MoC' + str((month % 12) + 1)
                })
            else:
                moc_month.update({
                    'start_date': timezone.datetime.date(datetime.datetime(year.year, month, constants.MOC_START_DATE)),
                    'end_date': timezone.datetime.date(datetime.datetime(year.year, month + 1, constants.MOC_END_DATE)),
                    'name': 'MoC' + str((month % 12) + 1)
                })
            moc = MoCMonth(**moc_month)
            print(moc.name)
            moc_months.append(moc)
        MoCMonth.objects.bulk_create(moc_months)
