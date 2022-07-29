'''
Offers import utility
'''
import datetime as dt
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from app.import_users import ErrorMessages, ImportProcess
from app.models import ShaktiEntrepreneur
from product.models import Product
from product.import_products import ImportProduct
from offers.models import (ShaktiBonus, ShaktiBonusLines, ShaktiPromotionLines, ShaktiPromotions,
                           MAX_DISCOUNT, DiscountType, Promotions, PromotionLines)


class ImportOffers(ImportProcess):

    def __init__(self):
        self.error_list = []
        self.updated = 0
        self.inserted = 0

    def process_file(self, request, imported_data):
        for index in range(len(imported_data)):
            row = imported_data[index]
            line_num = index + 1
            try:
                shakti_bonus_obj, created = self.get_create_shakti_bonus(
                    row, line_num)

                offers_count = shakti_bonus_obj.shaktibonuslines_set.values().count()
                bonus_objs = []

                if int(row[4]) > MAX_DISCOUNT or int(row[6]) > MAX_DISCOUNT or int(row[8]) > MAX_DISCOUNT:
                    raise StandardError(
                        'Discount cannot be more than %s' % MAX_DISCOUNT)
                if row[3] != '' and row[4] != '':
                    bonus_objs.append(ShaktiBonusLines(
                        shakti_bonus=shakti_bonus_obj,
                        target_amount=row[3],
                        discount=row[4]
                    ))

                if row[5] != '' and row[6] != '':
                    bonus_objs.append(ShaktiBonusLines(
                        shakti_bonus=shakti_bonus_obj,
                        target_amount=row[5],
                        discount=row[6],
                    ))

                if row[7] != '' and row[8] != '':
                    bonus_objs.append(ShaktiBonusLines(
                        shakti_bonus=shakti_bonus_obj,
                        target_amount=row[7],
                        discount=row[8]))

                bonus_count = len(bonus_objs)

                if abs(offers_count - bonus_count) <= bonus_count:
                    try:
                        ShaktiBonusLines.objects.bulk_create(bonus_objs)
                        if created:
                            self.inserted += 1
                        else:
                            self.updated += 1
                    except IntegrityError as error:
                        self.error_list.append(
                            "Error on line no. %s %s" % (line_num, error.message))
                    except StandardError as error:
                        self.error_list.append(
                            "Error on line no. %s %s" % (line_num, error.message))
                else:
                    self.error_list.append(
                        "Error on line no. %s %s" % (line_num, 'Please remove Shakti Bonus Lines to add more'))
            except StandardError as error:
                self.error_list.append(
                    "Error on line no. %s %s" % (line_num, error.message))

        impro = ImportProduct()
        impro.show_messages(request, int(self.inserted), int(self.updated))

        return self.error_list

    def process_offers(self, request, imported_data):
        '''process trade offers '''

        for index in range(len(imported_data)):
            row = imported_data[index]
            line_num = index + 1
            try:
                promotion_obj, created = self.get_create_bonus(
                    row, line_num)

                if int(row[5]) > MAX_DISCOUNT:
                    raise StandardError(
                        'Discount cannot be more than %s' % MAX_DISCOUNT)

                if row[3] != '' and row[4] != '' and row[5] != '':
                    obj, created = PromotionLines.objects.update_or_create(promotion=promotion_obj,
                                                                           buy_product__basepack_code=row[3].strip(
                                                                           ),
                                                                           defaults={
                                                                               'buy_product': Product.objects.filter(basepack_code=row[3].strip()).first(),
                                                                               'buy_quantity': row[4],
                                                                               'discount': row[5]})

                    if created:
                        self.inserted += 1
                    else:
                        self.updated += 1
                else:
                    self.error_list.append(
                        "Error on line no. %s %s" % (line_num, 'Please check values for Basepack Code, Buy Quantity, Discount '))
            except StandardError as error:
                self.error_list.append(
                    "Error on line no. %s %s" % (line_num, error.message))

        impro = ImportProduct()
        impro.show_messages(request, int(self.inserted), int(self.updated))

        return self.error_list

    def get_create_bonus(self, data, line_num):
        try:
            start_date = dt.datetime.strptime(data[1], '%m/%d/%Y')
            end_date = dt.datetime.strptime(data[2], '%m/%d/%Y')
            obj, created = Promotions.objects.get_or_create(
                name=data[0],
                start=start_date,
                end=end_date,
                defaults={
                    'discount_type': DiscountType.TRADE_OFFER
                })

            if not created:
                obj.start = start_date
                obj.end = end_date
                obj.save()

            return obj, created

        except ValueError as error:
            raise StandardError(error.message)
        except StandardError as error:
            raise StandardError(error.message)

    def get_create_shakti_bonus(self, data, line_num):
        shakti_obj = ShaktiEntrepreneur.objects.filter(code=data[0]).first()
        if shakti_obj is None:
            raise StandardError('Enter Valid Shakti Entrepreneur Code')
        try:
            start_date = dt.datetime.strptime(data[1], '%m/%d/%Y')
            end_date = dt.datetime.strptime(data[2], '%m/%d/%Y')
            obj, created = ShaktiBonus.objects.get_or_create(
                shakti_enterpreneur=shakti_obj,
                defaults={
                    'start': start_date,
                    'end': end_date})

            if not created:
                obj.start = start_date
                obj.end = end_date
                obj.save()

            return obj, created

        except ValueError as error:
            raise StandardError(error.message)
        except StandardError as error:
            raise StandardError(error.message)


class ImportPromotions(object):

    def __init__(self):
        self.error_list = []
        self.updated = 0
        self.inserted = 0

    def process_file(self, request, imported_data):
        for index in range(len(imported_data)):
            row = imported_data[index]
            line_num = index + 1
            try:
                shakti_promotion_obj, created = self.get_create_shakti_promotion(
                    row, line_num)
                shaktipromotionline = ShaktiPromotionLines(
                    promotion=shakti_promotion_obj,
                    buy_product=Product.objects.filter(
                        basepack_code__exact=(row[4].encode('utf-8')).strip()).first(),
                    buy_quantity=row[5],
                    discount=row[6]
                )
                shaktipromotionline.save()
            except StandardError as error:
                self.error_list.append(
                    "Error on line no. %s %s" % (line_num, error.message))

        return self.error_list

    def get_create_shakti_promotion(self, data, line_num):
        shakti_obj = ShaktiEntrepreneur.objects.filter(
            code__exact=data[1].strip()).first()
        if shakti_obj is None:
            raise StandardError('Enter Valid Shakti Entrepreneur Code')
        try:
            start_date = dt.datetime.strptime(data[2], '%m/%d/%Y')
            end_date = dt.datetime.strptime(data[3], '%m/%d/%Y')
            obj, created = ShaktiPromotions.objects.get_or_create(
                shakti_enterpreneur=shakti_obj,
                start=start_date,
                end=end_date,
                defaults={
                    'name': data[0],
                    'start': start_date,
                    'end': end_date})

            if not created:
                obj.start = start_date
                obj.end = end_date
                obj.save()

            return obj, created

        except ValueError as error:
            raise StandardError(error.message)
        except StandardError as error:
            raise StandardError(error.message)
