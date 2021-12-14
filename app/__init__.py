from flask import Flask, send_file
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from io import BytesIO
import os
from urllib.parse import quote


HORIZONTAL_PADDING = 6


app = Flask(__name__)


@app.route('/')
def get_analytic_xlsx_file():
    analyzer = AnalyticFileGen(
        host=os.getenv('DB_HOST'),
        username=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        db=os.getenv('DB_NAME'),
    )
    output = analyzer.export_xlsx()
    analyzer.dispose()

    return send_file(
        output,
        attachment_filename='gen_z_questionnaire_data.xlsx',
        as_attachment=True,
    )


class AnalyticFileGen:
    def __init__(self, host: str, username: str, password: str, db: str = 'zcmu_survey'):
        db_url = 'mysql+pymysql://{username}:{password}@{host}:3306/{db}'.format(
            username=quote(username),
            password=quote(password),
            host=quote(host),
            db=quote(db),
        )

        self.engine = create_engine(db_url)

    def dispose(self):
        self.engine.dispose()

    def export_xlsx(self):
        report_df = self.__get_analytic_report()
        output = write_xlsx_with_auto_adjust_width(
            sheet_name='data', df=report_df)
        return output

    def __get_analytic_report(self):
        answers_df = self.__get_answers()
        questions = answers_df[['question', 'anstype']].drop_duplicates()
        dfs = []

        for _, row in questions.iterrows():
            df = create_answer_by_type(row.anstype, row.question, answers_df)

            if df is not None:
                dfs.append(df)

        # Concat each question as column and expand horizontally
        report_df = pd.concat(dfs, axis=1)

        # Add a col of group
        groups_df = get_groups_from_answers(answers_df)
        report_df = add_a_multi_idx_col_to_origin(
            origin_df=report_df,
            source_df=groups_df,
            new_col_name='กลุ่ม',
        )

        # Fill-na only numberic columns
        numeric_cols = report_df.select_dtypes(include=['number']).columns
        report_df[numeric_cols] = report_df[numeric_cols].convert_dtypes().fillna(0)

        return report_df

    def __get_answers(self):
        responses_df = self.__get_responses()
        response_details_df = self.__get_response_details()
        response_options_df = self.__get_response_options()
        sections_df = self.__get_sections()

        # TODO: Checking number of rows of each Dataframe
        # The number of rows of response should be at least 1!

        detail_option_df = pd.merge(
            response_details_df, response_options_df, on="detail_id", how="left")
        answers_df = pd.merge(
            responses_df, detail_option_df, on="response_code", how="left")
        answers_df = pd.merge(
            answers_df, sections_df, on="section_id", how="left")

        return answers_df

    def __get_responses(self):
        query = 'SELECT * FROM response WHERE answer_group IS NOT NULL'
        return pd.read_sql(
            query,
            con=self.engine,
            parse_dates=["lastupdate"],
            index_col="response_code"
        )

    def __get_response_details(self):
        return pd.read_sql(
            'SELECT * FROM response_detail',
            con=self.engine,
            index_col="detail_id"
        )

    def __get_response_options(self):
        return pd.read_sql(
            'SELECT * FROM response_option',
            con=self.engine,
            index_col="detail_id"
        )

    def __get_sections(self):
        return pd.read_sql(
            'SELECT * FROM section',
            con=self.engine,
            index_col="section_id"
        )


def create_answer_by_type(answer_type: str, question: str, source: pd.DataFrame):
    if answer_type == 'ans_m':
        return create_multi_choice_answer(question, source)
    elif answer_type == 'ans_o':
        return create_one_choice_answer(question, source)
    elif answer_type == 'ans_r':
        return create_ranking_choice_answer(question, source)
    elif answer_type == 'ans_t':
        return create_input_answer(question, source)
    elif answer_type == 'ans_w':
        return create_weight_answer(question, source)
    return None


def create_multi_choice_answer(question_label: str, source: pd.DataFrame, choices_description="1=เลือก\n0=ไม่เลือก"):
    df = source[source.question == question_label].copy()

    df.loc[:, 'weight'] = pd.to_numeric(
        df.loc[:, 'weight'], downcast="integer")

    # Select only relevant columns and also rename
    df = df[['response_code', 'question', 'answer_y', 'weight']]
    col_names = ['response_code', 'question', 'answer', 'weight']
    df.columns = col_names

    df.answer.fillna(value="อื่นๆ", inplace=True)

    df = pd.pivot_table(df, index="response_code",
                        columns="answer", values='weight', fill_value=0)

    # choices_description = "0=ไม่เลือก\n1=เลือก"
    df.columns = pd.MultiIndex.from_product(
        [[question_label], df.columns,  [choices_description]])

    return df


def create_one_choice_answer(question_label: str, source: pd.DataFrame):
    df = source[source.question == question_label].copy()

    section_name = df.iloc[0]['section_name']

    df.loc[:, 'weight'] = df.loc[:, 'weight'].fillna(value=0)
    df.loc[:, 'weight'] = pd.to_numeric(
        df.loc[:, 'weight'], downcast="integer")

    # Replace NaN before generate choices
    df.answer_y.fillna(value='อื่นๆ', inplace=True)

    choices = sorted(pd.unique(df['answer_y']))
    choices_mapper = dict((v, i + 1) for i, v in enumerate(choices))
    choices_description = "\n".join(
        ["{}={}".format(i[1], i[0]) for i in choices_mapper.items()])
    choices_description += "\n0=ไม่ตอบ"

    # Select only selected answer(weight = 1), relevant columns
    df = df[df.weight == 1][['response_code', 'answer_y']]

    col_names = ['response_code', 'answer']
    df.columns = col_names

    df.drop_duplicates(inplace=True)
    df.set_index('response_code', inplace=True)

    # Covert text's answer to code
    df.replace({'answer': choices_mapper}, inplace=True)

    df.columns = pd.MultiIndex.from_product(
        [[section_name], [question_label], [choices_description]])

    return df

    # all_answer_pivot_df = pd.pivot_table(all_answer_df, index="response_code", columns="answer", values='weight', fill_value=0)

    # return all_answer_pivot_df


def create_ranking_choice_answer(question_label: str, source: pd.DataFrame):
    weights = pd.to_numeric(
        source[source.question == question_label]['weight'])
    max_weight = np.max(weights)

    choices_description = "[1-{}]=ค่าน้ำหนัก\n0=ไม่เลือก".format(
        int(max_weight))

    df = create_multi_choice_answer(
        question_label, source, choices_description)

    return df


def create_input_answer(question_label: str, source: pd.DataFrame):
    df = source[source.question == question_label].copy()

    section_name = df.iloc[0]['section_name']

    # Select only relevant columns
    df = df[['response_code', 'answer_x']]

    col_names = ['response_code', 'answer']
    df.columns = col_names

    df.answer.fillna(value="", inplace=True)
    df.drop_duplicates(inplace=True)
    df.set_index('response_code', inplace=True)

    # Try to covert to integer if possible, otherwise keep the original data-type
    df = df.astype(int, errors="ignore").convert_dtypes()

    choices_description = "#"
    df.columns = pd.MultiIndex.from_product(
        [[section_name], [question_label], [choices_description]])

    return df


def create_weight_answer(question_label: str, source: pd.DataFrame):
    df = source[source.question == question_label].copy()

    section_name = df.iloc[0]['section_name']

    df.loc[:, 'weight'] = df.loc[:, 'weight'].fillna(value=0)
    df.loc[:, 'weight'] = pd.to_numeric(
        df.loc[:, 'weight'], downcast="integer")

    # Select only selected answer(weight = 1), relevant columns
    df = df[['response_code', 'weight']]

    df.drop_duplicates(inplace=True)
    df.set_index('response_code', inplace=True)

    choices_description = "5=มากที่สุด\n4=มาก\n3=ปานกลาง\n2=น้อย\n1=น้อยที่สุด\n0=ไม่ตอบ"
    df.columns = pd.MultiIndex.from_product(
        [[section_name], [question_label], [choices_description]])

    return df


def write_xlsx_with_auto_adjust_width(sheet_name: str, df: pd.DataFrame):
    output = BytesIO()

    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    startrow = df.columns.nlevels
    startcol = df.index.nlevels
    df.to_excel(writer, sheet_name=sheet_name, header=False, startrow=startrow)

    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    worksheet.set_zoom(90)

    index_column_width = len(df.index.name) + HORIZONTAL_PADDING
    worksheet.set_column(0, 0, index_column_width)

    header_format = workbook.add_format({
        'bold': True,
        'border': 1,
        'align': 'center',
        'valign': 'top',
    })
    vertical_header_format = workbook.add_format({
        'bold': True,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
    })
    choice_description_format = workbook.add_format({
        'text_wrap': True,
        'indent': 1,
        'bold': True,
        'border': 1,
        'align': 'left',
        'valign': 'top',
    })

    worksheet.write(startrow, 0, df.index.name, header_format)

    # Auto-adjust columns' width
    for column in df:
        column_width = len(column[1]) + HORIZONTAL_PADDING
        col_idx = df.columns.get_loc(column) + 1
        worksheet.set_column(col_idx, col_idx, column_width)

    # Manually write headers
    for column in df:
        col_idx = df.columns.get_loc(column) + startcol
        worksheet.write(0, col_idx, column[0], header_format)
        worksheet.write(1, col_idx, column[1], header_format)
        worksheet.write(2, col_idx, column[2], choice_description_format)

    # Merge headers
    first_col_idx = df.index.nlevels
    last_col_num = len(df.columns) - 1

    head_header = None

    # Write main headers
    for col_num, column in enumerate(df.columns):
        if head_header is None:
            head_header = column[0]

        tail_header = column[0]
        col_idx = col_num + startcol
        prev_col_idx = col_idx - 1

        if tail_header != head_header:
            worksheet.merge_range(0, first_col_idx, 0,
                                  prev_col_idx, column[0], header_format)
            # Reset
            first_col_idx = col_idx
            head_header = tail_header

        if col_num == last_col_num:
            worksheet.merge_range(0, first_col_idx, 0,
                                  col_idx, column[0], header_format)

        # Check if column names of all index 0 - 2 vertically are same
        # then merge cells with vertical header style
        if column[0] == column[1] == column[2]:
            worksheet.merge_range(0, col_idx, 2, col_idx,
                                  column[0], vertical_header_format)

    writer.close()

    # go back to the beginning of the stream
    output.seek(0)

    return output


def get_groups_from_answers(from_df: pd.DataFrame):
    from_df = from_df.copy()

    group_idx = 'response_code'
    group_cols = ['response_code', 'answer_group']

    groups_df = from_df[group_cols].drop_duplicates(
    ).set_index(group_idx)

    return groups_df


def add_a_multi_idx_col_to_origin(origin_df: pd.DataFrame, source_df: pd.DataFrame, new_col_name: str):
    multi_idx_cols = [(new_col_name, new_col_name, new_col_name)]
    source_df.columns = pd.MultiIndex.from_tuples(multi_idx_cols)
    return pd.merge(source_df, origin_df, on="response_code", how="left")
