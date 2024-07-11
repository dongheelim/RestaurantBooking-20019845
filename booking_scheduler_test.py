import unittest
from unittest.mock import Mock, patch

from datetime import datetime, timedelta

from booking_scheduler import BookingScheduler
from schedule import Customer, Schedule

NOT_ON_THE_HOUR = datetime.strptime("2021/03/26 09:05", "%Y/%m/%d %H:%M")
ON_THE_HOUR = datetime.strptime("2021/03/26 09:00", "%Y/%m/%d %H:%M")
#CUSTOMER = Customer("Fake name", "010-1234-5678")
#CUSTOMER_WITH_MAIL = Customer("Fake name", "010-1234-5678", "test@test.com")
CUSTOMER = Mock()
CUSTOMER.get_email.return_value = None
CUSTOMER_WITH_MAIL = Mock()
CUSTOMER_WITH_MAIL.get_email_return_value = "test@test.com"
UNDER_CAPACITY = 1
CAPACITY_PER_HOUR = 3


class TestableScheduler(BookingScheduler):
    def __init__(self, capacity_per_hour, date_time):
        super().__init__(capacity_per_hour)
        self.__date_time = date_time

    def get_now(self):
        return datetime.strptime(self.__date_time, "%Y/%m/%d %H:%M")


class BookingSchedulerTest(unittest.TestCase):

    def setUp(self):
        self.booking_scheduler = BookingScheduler(CAPACITY_PER_HOUR)

        #self.testable_sms_sender = TestableSmsSender()
        self.sms_sender = Mock()
        self.booking_scheduler.set_sms_sender(self.sms_sender)

        #self.testable_mail_sender = TestableMailSender()
        self.mail_sender = Mock()
        self.booking_scheduler.set_mail_sender(self.mail_sender)

        super().setUp()

    def test_예약은_정시에만_가능하다_정시가_아닌경우_예약불가(self):
        schedule = Schedule(NOT_ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER)
        with self.assertRaises(ValueError):
            self.booking_scheduler.add_schedule(schedule)

    def test_예약은_정시에만_가능하다_정시인_경우_예약가능(self):
        schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER)
        self.booking_scheduler.add_schedule(schedule)

        self.assertTrue(self.booking_scheduler.has_schedule(schedule))

    def test_시간대별_인원제한이_있다_같은_시간대에_Capacity_초과할_경우_예외발생(self):
        schedule = Schedule(ON_THE_HOUR, CAPACITY_PER_HOUR, CUSTOMER)
        self.booking_scheduler.add_schedule(schedule)

        with self.assertRaises(ValueError) as context:
            new_schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER)
            self.booking_scheduler.add_schedule(new_schedule)

        self.assertEqual("Number of people is over restaurant capacity per hour", str(context.exception))

    def test_시간대별_인원제한이_있다_같은_시간대가_다르면_Capacity_차있어도_스케쥴_추가_성공(self):
        schedule = Schedule(ON_THE_HOUR, CAPACITY_PER_HOUR, CUSTOMER)
        self.booking_scheduler.add_schedule(schedule)

        different_hour = ON_THE_HOUR + timedelta(hours=1)
        new_schedule = Schedule(different_hour, UNDER_CAPACITY, CUSTOMER)
        self.booking_scheduler.add_schedule(new_schedule)

        self.assertTrue(self.booking_scheduler.has_schedule(schedule))

    def test_예약완료시_SMS는_무조건_발송(self):
        schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER)
        self.booking_scheduler.add_schedule(schedule)

        #self.assertTrue(self.sms_sender.is_send_method_is_called())
        self.sms_sender.send.assert_called()

    def test_이메일이_없는_경우에는_이메일_미발송(self):
        schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER)

        self.booking_scheduler.add_schedule(schedule)

        # self.assertEqual(self.mail_sender.get_count_send_mail_is_called(), 0)
        self.mail_sender.send_mail.assert_not_called()

    def test_이메일이_있는_경우에는_이메일_발송(self):
        schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER_WITH_MAIL)

        self.booking_scheduler.add_schedule(schedule)

        # self.assertEqual(self.mail_sender.get_count_send_mail_is_called(), 1)
        self.mail_sender.send_mail.assert_called_once()

    @patch.object(BookingScheduler, "get_now", return_value=datetime.strptime("2024/7/7 17:00", "%Y/%m/%d %H:%M"))
    def test_현재날짜가_일요일인_경우_예약불가_예외처리(self, mock):
        self.booking_scheduler = BookingScheduler(CAPACITY_PER_HOUR)

        with self.assertRaises(ValueError):
            new_schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER_WITH_MAIL)
            self.booking_scheduler.add_schedule(new_schedule)
            self.fail()

    @patch.object(BookingScheduler, "get_now", return_value=datetime.strptime("2024/7/8 17:00", "%Y/%m/%d %H:%M"))
    def test_현재날짜가_일요일이_아닌경우_예약가능(self, mock):
        self.booking_scheduler = BookingScheduler(CAPACITY_PER_HOUR)

        new_schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER_WITH_MAIL)
        self.booking_scheduler.add_schedule(new_schedule)

        self.assertTrue(self.booking_scheduler.has_schedule(new_schedule))


if __name__ == '__main__':
    unittest.main()
