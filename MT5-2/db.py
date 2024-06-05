from pymongo import MongoClient

class MongoDBHandler:
    def __init__(self, db_name, trade_collection_name, daily_summary_collection_name):
        self.client = MongoClient('mongodb+srv://utbiz:utbiz@utbiz.pdnb9ro.mongodb.net/?retryWrites=true&w=majority&appName=utbiz')
        self.db = self.client[db_name]
        self.trade_collection = self.db[trade_collection_name]
        self.daily_summary_collection = self.db[daily_summary_collection_name]

    def log_trade(self, trade_log):
        self.trade_collection.insert_one(trade_log)

    def log_daily_summary(self, daily_summary):
        self.daily_summary_collection.insert_one(daily_summary)

    def print_trade_logs(self):
        print("Trade Logs:")
        for trade in self.trade_collection.find():
            print(trade)

    def print_daily_summaries(self):
        print("Daily Summaries:")
        for summary in self.daily_summary_collection.find():
            print(summary)
