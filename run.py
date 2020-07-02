from linkedinspider import LinkedinSpider
import time
import json
import pandas as pd
import logging
import re

# interval between every profile [seconds]
PROFILE_WAIT = 10
# rest time for every restart
RESTART_WAIT = 120
# restart for every RESTART_COUNT scrapy
RESTART_COUNT = 20
# time waited after blocked by google
BLOCKED_BY_GOOGLE_WAIT = 60 * 20

LOG_LEVEL = logging.DEBUG


config_filename = "config.json"
officer_lender_file_path = "data/officier_lender_lyn.xlsx"
log_file_path = "log/spider.log"
query_pattern = 'site:linkedin.com/in/ AND {} AND Bank'
re_query_pattern = 'site:linkedin.com/in/ AND (.*?) AND Bank'

# six columns: officer, name, linkedin, lender, info, profile_url
df = pd.read_excel(officer_lender_file_path, dtype="object")


logger = logging.getLogger("run")
logger.setLevel(LOG_LEVEL)
handler = logging.StreamHandler()
handler.setLevel(LOG_LEVEL)
formatter = logging.Formatter(
    "\n[%(asctime)s] %(filename)s %(funcName)s at line %(lineno)s [%(levelname)s] \n\t %(message)s\n")
handler.setFormatter(formatter)
logger.addHandler(handler)

f_handler = logging.FileHandler("log/console.log", mode='a')
f_handler.setLevel(LOG_LEVEL)
f_handler.setFormatter(formatter)
logger.addHandler(f_handler)


def prepare_query() -> list:
    """Prepare the query string from officer_lender_file

    Returns:
        list: A list of query strings for the spider to query in Google
    """
    officer_names = list(df['officer'])
    return [query_pattern.replace("{}", officer_name) for officer_name in officer_names]


def update(index, info):
    """Update the dataframe according to the info scraped from linkedin

    Args:
        index (int): row needed to be updatedq
        info (dict): contains the information needed to be populated into the dataframe
    """
    df.at[index, "name"] = info["name"]
    df.at[index, "linkedin"] = 1
    df.at[index, "info"] = info["info"]
    df.at[index, "profile_url"] = info["profile_url"]


def recover_from_log() -> list:
    """Extract queries which has been issued from the log file

    Returns:
        list: A list of issued queries
    """
    ans = []
    with open(log_file_path, 'r') as log:
        for line in log:
            match = re.search(re.compile(re_query_pattern), line)
            if match is not None:
                ans.append(match.group(0))
    if len(ans) != 0:
        ans.pop()
    return ans


def write_back():
    # Write back the dataframe in memory into orginal file with a new sheet
    # pylint: disable=abstract-class-instantiated
    with pd.ExcelWriter(officer_lender_file_path) as writer:
        df.to_excel(writer, sheet_name="updated", index=False)
    logger.info(f"{officer_lender_file_path} updated.")


if __name__ == "__main__":

    try:
        with open(config_filename, "r") as f:
            # user is a Python dict
            user = json.load(f)
            username = user["linkedin_username"]
            password = user["linkedin_password"]

            queries = prepare_query()
            issued_queries = recover_from_log()

            spider = LinkedinSpider(username, password)
            spider.login()

            last_query = ""
            count = 0
            sum = len(queries)
            for index, query in enumerate(queries):
                # if(count == 2):
                #     break

                # skip the duplicate
                if (query == last_query or query in issued_queries):
                    logger.info(f"Skip {index + 1}/{sum}")
                    continue
                else:
                    last_query = query

                profile_urls = spider.search(query)

                # if search banned by google, sleep for 20min and retry
                if (profile_urls == -1):
                    logger.error("Unexpected blocked by Google ...")
                    spider.restart(BLOCKED_BY_GOOGLE_WAIT)

                # handle search results
                if len(profile_urls) != 0:
                    info = spider.parseInfo(profile_urls[0])
                    update(index, info)
                    count = count + 1

                    logger.info(
                        f"{index + 1}/{sum}, {count}th profiles scraped")

                    if (count % RESTART_COUNT == 0):
                        write_back()
                        spider.restart(RESTART_WAIT)
                        spider.login()
                        continue

                time.sleep(PROFILE_WAIT)
            logger.info(f"{count} profiles scraped in total.")
            if(count == sum):
                logger.info("Congragulations, all done!")
            else:
                logger.info(
                    f"For some reason, you have {sum - count} profiles unfinised! Please check it!")
    except Exception as e:
        print(e)
    finally:
        try:
            write_back()
            if(spider is not None):
                spider.close()
        except Exception as e:
            print(e)
