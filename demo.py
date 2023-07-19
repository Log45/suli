"""
This file will be testing Galactica being used in tandem with pdf_parser to extract descriptions of chemical separations from research papers.
Author: Logan Endes https://github.com/Log45

Goals: Using few-shot CoT, answer these questions with different prompts
    - What is the target?
    - What is the target disolved in?
    - What is the resin (column) used?
    - What is the column eluted with?
    - What are the products?
    - (maybe) How long was the target irradiated?
    - (maybe) How long did the separation process take?
"""
import time

from pdf_parser import pdf_to_context
import galai as gal

keywords = {"separation", "Separation", "isolation", "Isolation", "chromatography", "Chromatograph", "ion exchange", "ion Exchange", "Ion Exchange", "Ion exchange",
            "eluted", "Eluted", "elution", "Elution", "elute", "Elute", "fraction", "Fraction", "resin", "Resin", "exchange", "Exchange", "acid", "Acid", "target", "Target"}

example_context = "After irradiation of 5 h, the 64Ni target was dissolved in 6 M hydrochloride acid, and then the solution was load to an anion exchange column to separate into different components. The 64Ni was washed out with 6 M HCl and collected for recycling. Due to the elevated cost of enriched 64Ni, recycling of the target material for re-use could reduce the production cost of 64Cu, without sacriﬁcing the quality of subsequent 64Cu production. When the eluted was switched to 1 M HCl, the ﬁrst band coming out was co-produced cobalt radioisotopes (approximately 1 mL), and the second was the 64Cu, which was collected and evaporated to dryness. The residue was dissolved in 0.1 M HCl for further use. The separation process of 64Cu took about 2.5 h after irradiation."

target_question = "What is the target material in the above reaction?"
target_example_answer = "Since they say: 'the 64Ni target was dissolved in 6 M hydrochloride acid', then 64Ni, or Nickel-64, must be the target."

acid_question = "What acid is the target material dissolved in during the above reaction?"
acid_example_answer = "Since they say: 'the 64Ni target was dissolved in 6 M hydrochloride acid', then 6M hydrochloride acid must be the acid used to dissolve the target."

resin_question = "What resin/column is the solution loaded into during the above reaction?"
resin_example_answer = "Since they say: 'the solution was load to an anion exchange column to separate into different components', and an 'anion exchange column' is a resin/column, then an anion exchange column must be the resin/column."

elution_question = "What acid is used in the elution during the above reaction?"
elution_example_answer = "Since they say: 'When the eluted was switched to 1 M HCl', then 1 M HCl must be the acid used in the elution."

products_question = "What are the products of the above reaction?"
products_example_answer = "Since they say: 'the ﬁrst band coming out was co-produced cobalt radioisotopes (approximately 1 mL), and the second was the 64Cu, which was collected', and the first and second bands represent products, then cobalt radioisotopes and 64Cu, or Copper-64, must be the products."

target_example = f"Context: {example_context}\n Question: {target_question}\n Answer: {target_example_answer}"
acid_example = f"Context: {example_context}\n Question: {acid_question}\n Answer: {acid_example_answer}"
resin_example = f"Context: {example_context}\n Question: {resin_question}\n Answer: {resin_example_answer}"
elution_example = f"Context: {example_context}\n Question: {elution_question}\n Answer: {elution_example_answer}"
products_example = f"Context: {example_context}\n Question: {products_question}\n Answer: {products_example_answer}"

questions = [target_question, acid_question, resin_question, elution_question, products_question]
questions_examples_dict = {target_question : target_example,
                           acid_question : acid_example,
                           resin_question : resin_example,
                           elution_question : elution_example,
                           products_question : products_example}

galactica_models = {"mini", "base", "standard", "large", "huge"}

answer_questions_dict = {}


def default_generate():
    """
    This function uses no filtering or accuracy techniques to act as a base benchmark for other techniques.
    
    The goal of this function is to use a large language model to analyze paragraphs and extract descriptions of chemical separations from chemistry research papers.

    Returns:
        Tuple: 
            generations: list of the full responses generated by the model (includes context and examples)
            answers: list of answers only generated by the model
            t: float representing the time it took for the function to run
    """
    t1 = time.perf_counter()
    contexts = pdf_to_context()
    model = gal.load_model("base")
    generations = []
    answers = []
    for context in contexts:
        for q in questions:
            example = questions_examples_dict[q]
            input = f"{example}\n Context: {context}\n Question: {q}\n Answer: "
            generation = model.generate(input, max_new_tokens=50)
            answer = generation[len(input):]
            # print(f"Answer: {answer} \n")
            answer_questions_dict[answer] = q
            generations.append(generation)
            answers.append(answer)
    t = time.perf_counter() - t1
    print(f"{len(answers)} generations in {t} seconds.")
    return generations, answers, t


def keyword_filter_generate():
    """
    This function uses keyword filtering only to make responses as efficient:
        keyword_filtering: Throws away all context paragraphs that don't contain any keywords specified in the keywords set at the top of the file.

    The goal of this function is to use a large language model to analyze paragraphs and extract descriptions of chemical separations from chemistry research papers.

    Returns:
        Tuple: 
            generations: list of the full responses generated by the model (includes context and examples)
            answers: list of answers only generated by the model
            t: float representing the time it took for the function to run
    """
    t1 = time.perf_counter()
    contexts = pdf_to_context()
    model = gal.load_model("base")
    generations = []
    answers = []
    for context in contexts:
        if len(set(context.split()).intersection(keywords)) > 0:
            for q in questions:
                example = questions_examples_dict[q]
                input = f"{example}\n Context: {context}\n Question: {q}\n Answer: "
                generation = model.generate(input, max_new_tokens=50)
                answer = generation[len(input):]
                # print(f"Answer: {answer} \n")
                answer_questions_dict[answer] = q
                generations.append(generation)
                answers.append(answer)
    t = time.perf_counter() - t1
    print(f"{len(answers)} generations in {t} seconds.")
    return generations, answers, t


def model_filter_generate():
    """
    This function uses model filtering only to be less wasteful in generating responses:
        model_filtering: Asks the model to determine if the context paragraph contains a chemical extraction and continues if 'yes' in generated in the response.

    The goal of this function is to use a large language model to analyze paragraphs and extract descriptions of chemical separations from chemistry research papers.

    Returns:
        Tuple: 
            generations: list of the full responses generated by the model (includes context and examples)
            answers: list of answers only generated by the model
            t: float representing the time it took for the function to run
    """
    t1 = time.perf_counter()
    contexts = pdf_to_context()
    model = gal.load_model("base")
    generations = []
    answers = []
    for context in contexts:
        c = f"Context: {context}\n Question: Yes or no, does the above context describe a chemical extraction?\n Answer: "
        filter = model.generate(c, max_new_tokens=20)
        answer = filter[len(c):]
        if "Yes" in answer or "yes" in answer:
            for q in questions:
                example = questions_examples_dict[q]
                input = f"{example}\n Context: {context}\n Question: {q}\n Answer: "
                generation = model.generate(input, max_new_tokens=50)
                answer = generation[len(input):]
                # print(f"Answer: {answer} \n")
                answer_questions_dict[answer] = q
                generations.append(generation)
                answers.append(answer)
    t = time.perf_counter() - t1
    print(f"{len(answers)} generations in {t} seconds.")
    return generations, answers, t


def keyword_model_generate():
    """
    This function combines two techniques to make responses as accurate as possible:
        keyword_filtering: Throws away all context paragraphs that don't contain any keywords specified in the keywords set at the top of the file.
        model_filtering: Asks the model to determine if the context paragraph contains a chemical extraction and continues if 'yes' in generated in the response.

    The goal of this function is to use a large language model to analyze paragraphs and extract descriptions of chemical separations from chemistry research papers.

    Returns:
        Tuple: 
            generations: list of the full responses generated by the model (includes context and examples)
            answers: list of answers only generated by the model
            t: float representing the time it took for the function to run
    """
    t1 = time.perf_counter()
    contexts = pdf_to_context()
    model = gal.load_model("base")
    generations = []
    answers = []
    for context in contexts:
        if len(set(context.split()).intersection(keywords)) > 0:
            c = f"Context: {context}\n Question: Yes or no, does the above context describe a chemical extraction?\n Answer: "
            filter = model.generate(c, max_new_tokens=20)
            answer = filter[len(c):]
            if "Yes" in answer or "yes" in answer:
                for q in questions:
                    example = questions_examples_dict[q]
                    input = f"{example}\n Context: {context}\n Question: {q}\n Answer: "
                    generation = model.generate(input, max_new_tokens=50)
                    answer = generation[len(input):]
                    # print(f"Answer: {answer} \n")
                    answer_questions_dict[answer] = q
                    generations.append(generation)
                    answers.append(answer)
    t = time.perf_counter() - t1
    print(f"{len(answers)} generations in {t} seconds.")
    return generations, answers, t


def keyword_model_expert_check_generate():
    """
    This function combines four techniques to make responses as accurate as possible:
        keyword_filtering: Throws away all context paragraphs that don't contain any keywords specified in the keywords set at the top of the file.
        model_filtering: Asks the model to determine if the context paragraph contains a chemical extraction and continues if 'yes' in generated in the response.
        expert_response: Asks the model to respond as if they are an expert at chemistry to try to make the response more accurate.
        check_response: Asks the model to double check their answer by confirming if their response is truthful/accurate.

    The goal of this function is to use a large language model to analyze paragraphs and extract descriptions of chemical separations from chemistry research papers.

    Returns:
        Tuple: 
            generations: list of the full responses generated by the model (includes context and examples)
            answers: list of answers only generated by the model
            t: float representing the time it took for the function to run
    """
    t1 = time.perf_counter()
    contexts = pdf_to_context()
    model = gal.load_model("base")
    generations = []
    answers = []
    for context in contexts:
        if len(set(context.split()).intersection(keywords)) > 0:
            c = f"Context: {context}\n Question: Yes or no, does the above context describe a chemical extraction?\n Answer: "
            filter = model.generate(c, max_new_tokens=20)
            answer = filter[len(c):]
            if "Yes" in answer or "yes" in answer:
                for q in questions:
                    example = questions_examples_dict[q]
                    input = f"{example}\n Context: {context}\n Question: {q}\n Respond as if you are an expert at chemistry.\n Answer: "
                    generation = model.generate(input, max_new_tokens=50)
                    answer = generation[len(input):]
                    # print(f"Answer: {answer} \n")
                    # check = f"In regards to the context, {context}, is it correct to say that the response: {answer} is the correct evaluation of the question: {q} \n Respond yes or no: "
                    check = f"Question: Answer yes or no: is the response, '{answer}' a truthful statement in regards to the context '{context}'? \n Answer:"
                    gen = model.generate(check, max_new_tokens=20)
                    confirm = gen[len(check):]
                    print(confirm)
                    answer_questions_dict[answer] = q
                    if "yes" in confirm or "Yes" in confirm:
                        generations.append(generation)
                        answers.append(answer)
    t = time.perf_counter() - t1
    print(f"{len(answers)} generations in {t} seconds.")
    return generations, answers, t


def write_to_file(output_name = "keyword_model_expert_check_output.txt", filter = keyword_model_expert_check_generate):
    """_summary_

    Args:
        output_name (str, optional): _description_. Defaults to "keyword_filter_output.txt".
        filter (_type_, optional): _description_. Defaults to keyword_filter_generate.
    """
    _gen, _ans, _time = filter()

    _time = round(_time, 2)

    k = f"Generated {len(_gen)} responses in {_time} seconds."
    for i in range(len(_gen)):
        ans_idx = _gen[i].index('Answer:')
        gen = _gen[i][ans_idx:]
        gen = gen[gen.index('Context:'):]
        question_index = gen.index('Question:')
        ans = _ans[i]
        if i % 5 == 0:
            #j = 0
            # print(i)
            k += "\n\n\n" + gen[:question_index] + "\n"
        #q = questions[j]
        q = answer_questions_dict[ans]
        if q == questions[4]:
            k += "\nQuestion: " + q + "\nAnswe" + ans.split("\n")[0] + "\n"
        else:
            k += "\nQuestion: " + q + "\nAnswer" + ans.split("\n")[0] + "\n"
        # print(q)
        """
        if j % 4 == 0 and j != 0:
            k += "\nQuestion: " + q + "\nAnswe" + ans.split("\n")[0] + "\n"
        else:
            k += "\nQuestion: " + q + "\nAnswer" + ans.split("\n")[0] + "\n"
        # print(k)
        """
        #j += 1

    with open(f"output/{output_name}" if '.txt' in output_name else f"output/{output_name}.txt", "w", encoding="utf-8") as f:
         f.write(k)


def main():
    """"""
    write_to_file()
    # write_to_file("default_output", default_generate)
    # write_to_file("keyword_filter_output", keyword_filter_generate)
    # write_to_file("model_filter_output", model_filter_generate)
    # write_to_file("keyword_model_output", keyword_model_generate)


if __name__ == "__main__":
    main()
