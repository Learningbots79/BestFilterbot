import pyrogram
from pymongo import MongoClient
from configs import DATABASE_URI, DATABASE_NAME

class Database:

    def __init__(self):
        self.client0 = MongoClient(DATABASE_URI)
        self.client0 = self.client0[DATABASE_NAME]
        self.client1 = self.client0["FILTERS"]
        self.client2 = self.client0["CONNECTION"]
        self.client3 = self.client0["USERS"]

    def new_user(self, name, id):
        return dict(name=name, id=id, ban_status=dict(is_banned=False, ban_reason=""))

    # save new user     
    async def add_user(self, name, id):
        user = self.new_user(name, id)
        self.client3.insert_one(user)

    # is user exist       
    async def is_user_exist(self, id):
        data = {'id': int(id)}
        user = self.client3.find_one(data)
        return bool(user)

    # total number of save users
    async def total_users_count(self):
        count = self.client3.count()
        return count

    async def get_all_users(self):
        return self.client3.find()

    async def delete_user(self, id):
        await self.client3.delete_many({'id': id})
 
    async def add_filter(self, grp_id, text, reply_text, btn, file, alert):
        mycol = self.client1[str(grp_id)]
        data = { 'text':str(text), 'reply':str(reply_text), 'btn':str(btn), 'file':str(file), 'alert':str(alert) }
        try:
            mycol.update_one({'text': str(text)},  {"$set": data}, upsert=True)
        except:
            print('Couldnt save, check your db')

    async def get_filters(self, group_id):
        mycol = self.client1[str(group_id)]

        texts = []
        query = mycol.find()
        try:
            for file in query:
                text = file['text']
                texts.append(text)
        except:
            pass
        return texts

    async def find_filter(self, group_id, name):
        mycol = self.client1[str(group_id)]
    
        query = mycol.find( {"text":name})
        try:
            for file in query:
                reply_text = file['reply']
                btn = file['btn']
                fileid = file['file']
                try:
                    alert = file['alert']
                except:
                    alert = None
            return reply_text, btn, alert, fileid
        except:
            return None, None, None, None

    async def delete_filter(self, message, text, group_id):
        mycol = self.client1[str(group_id)]
    
        myquery = {'text':text }
        query = mycol.count_documents(myquery)
        if query == 1:
            mycol.delete_one(myquery)
            await message.reply_text(f"'`{text}`'  deleted. I'll not respond to that filter anymore.", quote=True, parse_mode=pyrogram.enums.ParseMode.MARKDOWN)
        else:
            await message.reply_text("Couldn't find that filter!", quote=True)

    async def del_all(self, message, group_id, title):
        if str(group_id) not in self.client1.list_collection_names():
            await message.edit_text(f"Nothing to remove in {title}!")
            return
        
        mycol = self.client1[str(group_id)]
        try:
            mycol.drop()
            await message.edit_text(f"All filters from {title} has been removed")
        except:
            await message.edit_text(f"Couldn't remove all filters from group!")
            return

    async def count_filters(self, group_id):
        mycol = self.client1[str(group_id)]

        count = mycol.count()
        if count == 0:
            return False
        else:
            return count

    async def filter_stats(self):
        collections = self.client1.list_collection_names()

        if "CONNECTION" in collections:
            collections.remove("CONNECTION")

        totalcount = 0
        for collection in collections:
            mycol = mydb[collection]
            count = mycol.count()
            totalcount = totalcount + count

        totalcollections = len(collections)

        return totalcollections, totalcount


    async def add_connection(self, group_id, user_id):
        query = self.client2.find_one({ "_id": user_id }, { "_id": 0, "active_group": 0 })
        if query is not None:
            group_ids = []
            for x in query["group_details"]:
                group_ids.append(x["group_id"])

            if group_id in group_ids:
                return False

        group_details = {"group_id" : group_id}

        data = {'_id': user_id, 'group_details' : [group_details], 'active_group' : group_id}
    
        if self.client2.count_documents( {"_id": user_id} ) == 0:
            try:
                self.client2.insert_one(data)
                return True
            except:
                print('Some error occured!')

        else:
            try:
                self.client2.update_one({'_id': user_id}, { "$push": {"group_details": group_details}, "$set": {"active_group" : group_id} })
                return True
            except:
                print('Some error occured!')
    
    async def active_connection(self, user_id):
        query = self.client2.find_one({ "_id": user_id }, { "_id": 0, "group_details": 0 })
        if query:
            group_id = query['active_group']
            if group_id != None:
                return int(group_id)
            else:
                return None
        else:
            return None


    async def all_connections(self, user_id):
        query = self.client2.find_one({ "_id": user_id }, { "_id": 0, "active_group": 0 })
        if query is not None:
            group_ids = []
            for x in query["group_details"]:
                group_ids.append(x["group_id"])
            return group_ids
        else:
            return None


    async def if_active(self, user_id, group_id):
        query = self.client2.find_one({ "_id": user_id }, { "_id": 0, "group_details": 0 })
        if query is not None:
            if query['active_group'] == group_id:
                return True
            else:
                return False
        else:
            return False


    async def make_active(self, user_id, group_id):
        update = self.client2.update_one({'_id': user_id}, {"$set": {"active_group" : group_id}})
        if update.modified_count == 0:
            return False
        else:
            return True

    async def make_inactive(self, user_id):
        update = self.client2.update_one({'_id': user_id}, {"$set": {"active_group" : None}})
        if update.modified_count == 0:
            return False
        else:
            return True

    async def delete_connection(self, user_id, group_id):

        try:
            update = self.client2.update_one({"_id": user_id}, {"$pull" : { "group_details" : {"group_id":group_id} } })
            if update.modified_count == 0:
                return False
            else:
                query = self.client2.find_one({ "_id": user_id }, { "_id": 0 })
                if len(query["group_details"]) >= 1:
                    if query['active_group'] == group_id:
                        prvs_group_id = query["group_details"][len(query["group_details"]) - 1]["group_id"]

                        mycol.update_one({'_id': user_id},{"$set": {"active_group" : prvs_group_id}})
                else:
                    mycol.update_one({'_id': user_id}, {"$set": {"active_group" : None}})                    
                return True
        except Exception as e:
            print(e)
            return False

db = Database()
