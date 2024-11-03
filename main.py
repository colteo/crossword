#!/usr/bin/env python3

import argparse
import sys
import logging
from typing import Dict
from generators.type_a import TypeACrossword
from generators.type_b import TypeBCrossword
from generators.type_c import TypeCCrossword
from generators.hidden_word_a import HiddenWordAGenerator


def setup_logging(verbose: bool) -> None:
    """Configure logging level based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def get_db_config() -> Dict[str, str]:
    """Get database configuration from environment or use defaults."""
    return {
        'user': 'crossword',
        'password': 'crossword',
        'host': 'localhost',
        'database': 'crossword'
    }


def create_generator(generator_type: str, grid_size: int, cell_size: int, db_config: Dict[str, str]):
    """
    Factory function to create the appropriate generator based on type.

    Args:
        generator_type: Type of crossword generator to create
        grid_size: Size of the crossword grid
        cell_size: Size of each cell in pixels
        db_config: Database configuration dictionary

    Returns:
        An instance of the appropriate crossword generator
    """
    generators = {
        'type_a': TypeACrossword,
        'type_b': TypeBCrossword,
        'type_c': TypeCCrossword,
        'hidden': HiddenWordAGenerator
    }

    generator_class = generators.get(generator_type)
    if not generator_class:
        raise ValueError(f"Invalid generator type: {generator_type}")

    return generator_class(
        grid_size=grid_size,
        cell_size=cell_size,
        db_config=db_config
    )


def parse_args():
    """Parse and validate command line arguments."""
    parser = argparse.ArgumentParser(
        description='Crossword Puzzle Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -t type_a -s 15 --cell-size 75
  %(prog)s -t hidden -s 20 -v
  %(prog)s -t type_b --max-attempts 5
        """
    )

    parser.add_argument(
        '-t', '--type',
        choices=['type_a', 'type_b', 'type_c', 'hidden'],
        required=True,
        help='Type of crossword to generate'
    )

    parser.add_argument(
        '-s', '--size',
        type=int,
        default=15,
        help='Size of the grid (default: 15)'
    )

    parser.add_argument(
        '--cell-size',
        type=int,
        default=75,
        help='Size of each cell in pixels (default: 75)'
    )

    parser.add_argument(
        '--max-attempts',
        type=int,
        default=3,
        help='Maximum number of generation attempts (default: 3)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Validate grid size
    if args.size < 5 or args.size > 30:
        parser.error("Grid size must be between 5 and 30")

    # Validate cell size
    if args.cell_size < 20 or args.cell_size > 200:
        parser.error("Cell size must be between 20 and 200 pixels")

    # Validate max attempts
    if args.max_attempts < 1 or args.max_attempts > 10:
        parser.error("Maximum attempts must be between 1 and 10")

    return args


def main():
    """Main function to handle the crossword generation process."""
    try:
        args = parse_args()
        setup_logging(args.verbose)

        logging.info(f"Starting crossword generation with type: {args.type}")
        logging.info(f"Grid size: {args.size}x{args.size}")

        db_config = get_db_config()

        # Create the appropriate generator
        generator = create_generator(
            args.type,
            args.size,
            args.cell_size,
            db_config
        )

        # Set max attempts if different from default
        generator.max_attempts = args.max_attempts

        # Generate the crossword
        result = generator.generate_crossword()

        # Check the result
        if "Unable to generate" in result:
            logging.error(result)
            sys.exit(1)
        else:
            logging.info("Crossword generated successfully")
            logging.info(f"Output files are in: {generator.output_dir}")
            print(result)
            sys.exit(0)

    except KeyboardInterrupt:
        logging.info("\nGeneration cancelled by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Error during crossword generation: {str(e)}")
        if args.verbose:
            logging.exception("Detailed error information:")
        sys.exit(1)


if __name__ == "__main__":
    main()