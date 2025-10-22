import argparse
import re
import requests
import json
from utils import  read_warc_file, read_wet_file
from datasets import load_dataset
from typing import Set, Dict
import string

import html2text
import chardet
import regex as re

def retrieve_bad_words() -> set[str]:
    """Helper function - that reads a list of bad words from a file and returns them as a set.
    Returns:
        Set[str]: A set containing lowercase bad words.
    """
    with open('./bad_word_list.txt', 'r') as file:
        records = file.read().strip().split('\n')
        bad_words = [record.lower() for record in records]
        return set(bad_words)


def html_to_text(html) -> str:
    """Converts HTML content to plain text..
    Args:
        html (bytes): HTML content as bytes.
    Returns:
        str: Plain text extracted from HTML.
    """
    if isinstance(html, bytes):
        raw = bytes(html)
        det = chardet.detect(raw)
        enc = (det.get("encoding") or "utf-8").strip()
        html = html.decode(enc, errors='replace')
    # print("HTML:")
    # print(html)

    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = False
    h.images_to_alt = True
    h.inline_links = False
    h.ignore_tables=True
    h.ignore_emphasis = True
    h.ignore_links = True
    h.unicode_snob = True
    h.body_width = 0

    text = h.handle(html).strip()
    return text


def replace_pii(text: str) -> str:
    """Masks personally identifiable information (PII) from text with the specified masking formats.
    Args:
        text (str): Candidate text.
    Returns:
        str: Text with PII obfuscated.
    """
    # Replace US social security numbers (XXX-XX-XXXX format)
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    text = re.sub(ssn_pattern, 'XXX-XX-XXXX', text)
    
    # Replace 10-digit phone numbers prefixed with +1
    phone_pattern = r'\+1\d{10}\b'
    text = re.sub(phone_pattern, '+1XXXXXXXXXX', text)
    
    return text


def clean_text(text: str) -> str:
    """Removes substrings identified as low-quality according to alphanumeric, whitespace and valid document checks.
    Args:
        text (str): document to process.
    Returns:
        str: cleaned document
    """
    # Split the document into paragraphs
    paragraphs = text.split("\n")
    
    kept_paragraphs = []
    for paragraph in paragraphs:
        # Drop paragraphs that contain more than 100 alphanumeric characters with no whitespace between them
        if re.search(r'[a-zA-Z0-9]{101,}', paragraph):
            continue
            
        # Drop paragraphs that do not contain punctuation
        if not any(c in string.punctuation for c in paragraph):
            continue
            
        kept_paragraphs.append(paragraph)
    
    # Join the surviving paragraphs with newline characters in their original order
    cleaned = "\n".join(kept_paragraphs)
    return cleaned


def heuristic_quality_filter(text: str) -> bool:
    """Rejects documents based on the presence of bad words and punctuation.
    Args:
        text (str): document to check
    Returns:
        bool: returns True if the document passes the filters, False otherwise.
    """
    bad_words = retrieve_bad_words()
    lowered = text.lower()
    for bw in bad_words:
        if bw in lowered:
            return False
    
    # Check for non-whitespace content
    if len(text.strip()) == 0:
        return False
    
    # Must include at least one punctuation character
    punctuation = sum(c in string.punctuation for c in text)
    if punctuation == 0:
        return False
    
    # Check that 80% or more characters are alphanumeric, punctuation, or whitespace
    valid_chars = sum(c.isalnum() or c in string.punctuation or c.isspace() for c in text)
    if valid_chars / len(text) < 0.8:
        return False
    
    return True


def is_english_text(text: str) -> bool:
    """Detects if text is primarily in English based on character distribution.
    Args:
        text (str): Text to analyze
    Returns:
        bool: True if text is primarily English, False otherwise
    """
    english_letters = sum(c.isascii() and c.isalpha() for c in text)
    total_letters = sum(c.isalpha() for c in text)
    if total_letters == 0:
        return False
    return english_letters / total_letters > 0.9
    

def deduplicate_texts(texts: list[str]) -> list[str]:
    """Deduplicates text by removing duplicate sentences.
    Args:
        texts (list[str]): List of text strings to deduplicate.
    Returns:
        list[str]: Deduplicated list of texts. Implemented a simple Jaccard similarity based deduplication.
    """
    kept: list[str] = []
    kept_sets: list[set[str]] = []
    THRESH = 0.5

    for t in texts:
        tokens = re.findall(r'\w+', t.lower())
        tset = set(tokens)
        if not tset:
            continue

        duplicate = False
        for ks in kept_sets:
            inter = len(tset & ks)
            union = len(tset | ks) or 1
            jaccard = inter / union
            if jaccard >= THRESH:
                duplicate = True
                break

        if not duplicate:
            kept.append(t)
            kept_sets.append(tset)

    return kept


if __name__ == '__main__' :
    parser = argparse.ArgumentParser()
    parser.add_argument('--fname', type = str,  default = '', help = 'Specify the path for your warc file.')
    parser.add_argument('--dfname', type = str,  default = '', help = 'Specify the path where you stored topic_dataset.json')
    parser.add_argument('--num_records', type = int,  default=30, help = 'Specify the number of records you want to parse (only used for debugging with smaller sets)')
    parser.add_argument('--output', type = str,  default='cleaned_documents.txt', help = 'Output file for cleaned text documents')
    # parser.add_argument('--wet_name', type = str, default = '', help = 'Specify the path for your wet file.')
    args = parser.parse_args()

    if args.fname:
        seen = 0
        passes = 0

        with open(args.output, 'w', encoding='utf-8') as output_file:
            for url, html_text in read_warc_file(args.fname, args.num_records):
                seen += 1
                # print("Before HTML to text: ", str(html_text))
                text = html_to_text(html_text)
                # print("\n\n\nAfter HTML to text: ", text)
                cleaned_text = clean_text(text)
                # print("After cleaning: ", cleaned_text)
                cleaned_nopii_text = replace_pii(cleaned_text)
                # print("After PII removal: ", cleaned_nopii_text)
                passes_check = heuristic_quality_filter(cleaned_nopii_text)
                is_english = is_english_text(cleaned_nopii_text)
                print(url)
                print("Passes heuristic quality filter:", passes_check)
                print("Is English text:", is_english)
                if passes_check and is_english:
                    passes += 1
                    # Replace newlines with spaces to keep each document on one line
                    single_line_text = cleaned_nopii_text.replace('\n', ' ').replace('\r', ' ').strip()
                    output_file.write(single_line_text + '\n')
                    print("Saved cleaned English document to output file")
                elif passes_check and not is_english:
                    print("Document filtered out: not English")

        print(f"{passes} passed out of {seen} records processed.")
        print(f"Cleaned documents saved to: {args.output}")

    if args.dfname:
        with open(args.dfname, 'r') as f:
            raw_texts = json.load(f)
        raw_texts = [item['text'] for item in raw_texts['data']]
        deduplicated_texts = deduplicate_texts(raw_texts)
        print(f"{len(deduplicated_texts)} deduplicated out of {len(raw_texts)} records processed.")
    else:
        print("Usage: python homework.py --fname data.warc")